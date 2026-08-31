"""Append-only SQLite journal with raw bytes, hash chain and transactional batches."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3

from gallop.mobile import check_path
from .protocol import canonical, digest, now


class JournalConflict(ValueError):
    pass


class EventStore:
    def __init__(self, root, namespace):
        self.path = check_path(root / "events.sqlite3")
        self.namespace = namespace
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS raw_inputs(
                sha TEXT PRIMARY KEY, received_at TEXT NOT NULL, body BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS events(
                seq INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL,
                kind TEXT NOT NULL, timestamp TEXT NOT NULL, source TEXT NOT NULL,
                namespace TEXT NOT NULL, raw_sha TEXT REFERENCES raw_inputs(sha),
                payload TEXT NOT NULL, previous_hash TEXT NOT NULL, hash TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
                BEGIN SELECT RAISE(ABORT, 'append-only events'); END;
            CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
                BEGIN SELECT RAISE(ABORT, 'append-only events'); END;
            CREATE TRIGGER IF NOT EXISTS raw_no_update BEFORE UPDATE ON raw_inputs
                BEGIN SELECT RAISE(ABORT, 'immutable raw input'); END;
            CREATE TRIGGER IF NOT EXISTS raw_no_delete BEFORE DELETE ON raw_inputs
                BEGIN SELECT RAISE(ABORT, 'immutable raw input'); END;
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def raw(self, body):
        sha = hashlib.sha256(body).hexdigest()
        self.db.execute("INSERT OR IGNORE INTO raw_inputs VALUES (?,?,?)", (sha, now(), body))
        return sha

    def append(self, kind, identity, payload, *, at, source, raw_sha=None):
        event_id = kind + "-" + digest([self.namespace, identity])[:32]
        existing = self.db.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
        body = canonical(payload)
        if existing:
            if existing["payload"] != body or existing["timestamp"] != at or existing["source"] != source:
                raise JournalConflict("Stable event id reused with different content")
            return event_id, False
        last = self.db.execute("SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        event = dict(seq=last["seq"] + 1 if last else 1, event_id=event_id, kind=kind,
                     timestamp=at, source=source, namespace=self.namespace, raw_sha=raw_sha,
                     payload=payload, previous_hash=last["hash"] if last else "")
        event["hash"] = digest(event)
        self.db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)", (
            event["seq"], event_id, kind, at, source, self.namespace, raw_sha, body,
            event["previous_hash"], event["hash"]))
        return event_id, True

    def events(self):
        result, previous = [], ""
        raw_hashes = {}
        for row in self.db.execute("SELECT * FROM events ORDER BY seq"):
            event = dict(row)
            event["payload"] = json.loads(event["payload"])
            claimed = event.pop("hash")
            if (event["seq"] != len(result) + 1 or event["previous_hash"] != previous
                    or event["namespace"] != self.namespace or digest(event) != claimed):
                raise JournalConflict("Journal chain or namespace is inconsistent")
            if event["raw_sha"]:
                sha = event["raw_sha"]
                if sha not in raw_hashes:
                    raw = self.db.execute("SELECT body FROM raw_inputs WHERE sha=?", (sha,)).fetchone()
                    if raw is None or hashlib.sha256(raw[0]).hexdigest() != sha:
                        raise JournalConflict("Raw evidence is missing or altered")
                    raw_hashes[sha] = True
            event["hash"] = claimed
            previous = claimed
            result.append(event)
        return result
