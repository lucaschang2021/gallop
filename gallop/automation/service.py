"""Small single-writer application service. Every durable decision has an event."""
from contextlib import contextmanager
from datetime import date
import hashlib
import json
import os
from pathlib import Path

from gallop.adapters.deeptutor import DeepTutorAdapter
from gallop.core.io import atomic_json
from gallop.core.validation import validate_protocol
from gallop.mobile import check_path, export_mobile
from .protocol import digest, now, normalize_session, parse, synthetic, timestamp, validate_result
from .state import POLICIES, concept_key, replay, training_candidate
from .store import EventStore, JournalConflict
from .jobs import Jobs, file_lock


class Automation:
    def __init__(self, config):
        self.config = config
        config.bind()
        self.store = EventStore(config.root, config.namespace)
        self.cache = check_path(config.root / "derived-state.json")
        self._depth = 0

    def close(self):
        self.store.close()

    @contextmanager
    def lock(self):
        if self._depth:
            self._depth += 1
            try:
                yield
            finally:
                self._depth -= 1
            return
        path = check_path(self.config.root / "operation.lock")
        # Legacy locks have unknown ownership; preserve them for review.
        if path.exists():
            raise FileExistsError("Legacy operation.lock requires ownership review")
        with file_lock(self.config.root / ".writer.lock"):
            self._depth = 1
            try:
                self.config.validate()
                yield
            finally:
                self._depth = 0

    def state(self, *, check_cache=True):
        events = self.store.events()
        if check_cache and self.cache.exists():
            cached = json.loads(self.cache.read_text(encoding="utf-8"))
            seq = cached.get("seq")
            if type(seq) is not int or seq < 0 or seq > len(events) or replay(events[:seq]) != cached:
                raise JournalConflict("Derived state disagrees with its journal prefix; preserve it and investigate")
        return replay(events)

    def _mutate(self, operation):
        with self.lock():
            with self.store.transaction():
                self.state()
                result = operation()
                events = self.store.events()
                provisional = replay(events, verify=False)
                recorded = {digest(e["payload"]) for e in events if e["kind"] == "state_transition"}
                by_id = {e["event_id"]: e for e in events}
                for transition in provisional["transitions"]:
                    if digest(transition) not in recorded:
                        origin = by_id[transition["source_event"]]
                        self.store.append("state_transition", [transition["source_event"], transition["concept_key"]],
                                          transition, at=origin["timestamp"], source=origin["event_id"])
                final = replay(self.store.events())
            # Journal commit comes first. A crash here leaves a recoverable stale cache.
            if not self.cache.exists() or json.loads(self.cache.read_text(encoding="utf-8")) != final:
                atomic_json(check_path(self.cache), final)
            return result

    def _read_input(self, path):
        path = check_path(Path(path))
        raw = path.read_bytes()
        # Raw storage is intentionally separate, including rejected input.
        with self.store.transaction():
            sha = self.store.raw(raw)
        document = parse(raw)
        if self.config.namespace == "learner" and (
            synthetic(document) or any(p.lower() in {"integration_tests", "synthetic"} for p in path.parts)
        ):
            raise ValueError("Synthetic/integration input cannot enter learner state")
        return document, sha

    def intake(self, path):
        with self.lock():
            document, sha = self._read_input(path)
            session = normalize_session(document)
            def append():
                eid, added = self.store.append("session", session["session_id"], session,
                    at=session["occurred_at"], source="tutor:" + session["tutor"], raw_sha=sha)
                return {"event_id": eid, "duplicate": not added}
            result = self._mutate(append)
            self.refresh_queue()
            return result

    def _status(self, item, status, reason):
        allowed = {"queued": {"ready", "cancelled", "failed"}, "ready": {"in_progress", "cancelled", "failed"},
                   "in_progress": {"completed", "cancelled", "failed"},
                   "completed": set(), "failed": {"queued"}, "cancelled": set()}
        old = item["status"]
        if status not in allowed[old]:
            raise ValueError("Invalid training status transition")
        payload = dict(queue_id=item["queue_id"], **{"from": old, "to": status}, reason=reason)
        revision = sum(e["kind"] == "queue_status" and e["payload"]["queue_id"] == item["queue_id"]
                       for e in self.store.events()) + 1
        self.store.append("queue_status", [item["queue_id"], revision], payload,
                          at=now(), source="training-queue")

    def refresh_queue(self, *, day=None):
        day = day or date.today()
        def refresh():
            state = self.state()
            for concept in state["concepts"].values():
                completed_reviews = {q["review_key"] for q in state["queue"].values()
                                     if q["status"] == "completed" and q.get("review_key")
                                     and q["concept_key"] == concept_key(concept["subject"], concept["concept"])}
                candidate = training_candidate(concept, day, completed_reviews)
                related = [q for q in state["queue"].values() if q["concept_key"] == candidate["concept_key"]]
                if any(q["status"] in {"ready", "in_progress"} for q in related):
                    continue
                if candidate["queue_id"] in state["queue"]:
                    continue
                for previous in related:
                    if previous["status"] == "queued":
                        self._status(previous, "cancelled", "Superseded by newer evidence")
                self.store.append("queue_created", candidate["queue_id"], candidate,
                                  at=now(), source="deterministic-policy-v1")
            return None
        self._mutate(refresh)
        return self.queue()

    def queue(self):
        with self.lock():
            return sorted(self.state()["queue"].values(), key=lambda q: (q["priority"], q["created_at"], q["queue_id"]))

    def prepare(self, queue_id, *, send=False, engine=None, question_count=7, _defer=False):
        if send and engine is None:
            return self.submit(queue_id, question_count=question_count)
        if type(question_count) is not int or not 1 <= question_count <= 100:
            raise ValueError("Question count must be between 1 and 100")
        with self.lock():
            state = self.state()
            if queue_id in state["practices"]:
                prepared = state["practices"][queue_id]
                self._write_prepared(prepared)
                return prepared
            item = state["queue"][queue_id]
            if item["status"] != "queued":
                raise ValueError("Only queued work can be prepared")
            # Stable IDs do not depend on provider-generated UUIDs.
            manifest_id = "m-" + digest([self.config.namespace, queue_id])[:24]
            sessions = [(eid, s) for eid, s in state["sessions"].items() if eid in item["evidence_refs"]]
            course = sessions[-1][1]["course"] if sessions else ""
            manifest = dict(schema_version="1.0", manifest_id=manifest_id,
                session_id=sessions[-1][0] if sessions else item["evidence_refs"][0],
                subject=item["subject"], course=course, topic=item["concept"], concepts=[item["concept"]],
                weakness_tags=state["concepts"][item["concept_key"]]["weakness_tags"],
                mistakes=[], open_questions=state["concepts"][item["concept_key"]]["open_questions"],
                difficulty="hard" if item["training_type"] in {"proof", "hard_problem"} else "medium",
                practice_priority=int(item["priority"][1:]) + 1, source_notes=[],
                requested_question_count=question_count, practice_modes=[item["training_type"]],
                no_agent=True, hint_gradient=["independent_attempt", "direction_only", "key_observation",
                                             "skeleton", "full_solution"], created_at=now())
            validate_protocol("practice-manifest.schema.json", manifest)
            directory = check_path(self.config.root / "prepared" / queue_id)
            manifest_path = check_path(directory / "manifest.json")
            if manifest_path.exists():
                saved = json.loads(manifest_path.read_text(encoding="utf-8"))
                if {k: v for k, v in saved.items() if k != "created_at"} != {
                    k: v for k, v in manifest.items() if k != "created_at"
                }:
                    raise JournalConflict("Prepared manifest conflicts with the queue")
                manifest = saved
            else:
                atomic_json(manifest_path, manifest)
            task = {"practice_id": "p-" + digest([self.config.namespace, queue_id])[:24],
                    "manifest_id": manifest_id, "engine": "human-performance",
                    "questions": [], "answer_key": [],
                    "task": f"Independently perform {item['training_type']} on {item['concept']}. "
                            "Record your actual response and obtain human assessment; do not claim completion."}
            if _defer:
                return {"queue_id": queue_id, "manifest": manifest, "manifest_id": manifest_id,
                        "practice_id": task["practice_id"]}
            if send:
                if engine is None:
                    if self.config.deeptutor is None:
                        raise ValueError("DeepTutor executable is not configured")
                    engine = DeepTutorAdapter(self.config.deeptutor, home=self.config.deeptutor_home)
                try:
                    diagnostic = engine.generate(manifest)
                    if (diagnostic.get("manifest_id") != manifest_id or not isinstance(diagnostic.get("questions"), list)
                            or len(diagnostic["questions"]) != manifest["requested_question_count"] or
                            any(not isinstance(q, dict) or not q.get("prompt") for q in diagnostic["questions"])):
                        raise ValueError("Malformed DeepTutor result")
                    task.update(diagnostic_questions=diagnostic["questions"],
                                answer_key=diagnostic.get("answer_key", []), engine="deeptutor",
                                provider_practice_id=diagnostic["practice_id"])
                    task["notice"] = "Choice diagnostics are preparation, never proof/oral/coding assessment."
                except Exception:
                    self._mutate(lambda: self._status(item, "failed", "DeepTutor generation failed; no learner evidence"))
                    raise
            prepared = {"queue_id": queue_id, "manifest_id": manifest_id, "practice_id": task["practice_id"],
                        "manifest": manifest, "practice": task}
            def commit():
                self.store.append("prepared", queue_id, prepared, at=manifest["created_at"], source="deeptutor-bridge")
                self._status(item, "ready", "Prepared only; waiting for human start")
            self._mutate(commit)
            self._write_prepared(prepared)
            return prepared

    def submit(self, queue_id, *, question_count=7, retry=False, deadline=240):
        with self.lock():
            if self.config.deeptutor is None:
                raise ValueError("DeepTutor executable is not configured")
            if queue_id in self.state()["practices"]:
                raise ValueError("Practice already prepared; do not submit it again")
            pending = self.prepare(queue_id, question_count=question_count, _defer=True)
            adapter = DeepTutorAdapter(self.config.deeptutor, home=self.config.deeptutor_home)
            jobs = Jobs(self.config.root)
            job_id = jobs.prepare(queue_id, pending["manifest"], adapter)
            return jobs.submit(job_id, retry=retry, deadline=deadline)

    def poll(self, job_id):
        return Jobs(self.config.root).poll(job_id)

    def collect(self, job_id):
        with self.lock():
            status = self.poll(job_id)
            if status["status"] != "completed":
                return status
            diagnostic = status["completion"]["practice"]
            class Collected:
                def generate(self, manifest):
                    if manifest["manifest_id"] != diagnostic["manifest_id"]:
                        raise ValueError("Collected manifest mismatch")
                    return diagnostic
            already = status["queue_id"] in self.state()["practices"]
            if already and self.state()["practices"][status["queue_id"]]["practice"].get("provider_practice_id") != diagnostic["practice_id"]:
                raise JournalConflict("Queue already prepared from a different source")
            prepared = self.prepare(status["queue_id"], send=True, engine=Collected(),
                                    question_count=len(diagnostic["questions"]))
            return {"job_id": job_id, "status": "completed", "queue_id": status["queue_id"],
                    "manifest_id": prepared["manifest_id"], "practice_id": prepared["practice_id"],
                    "turn_id": status["completion"]["turn_id"], "duplicate": already}

    def _write_prepared(self, prepared):
        directory = check_path(self.config.root / "prepared" / prepared["queue_id"])
        task = prepared["practice"]
        for filename, value in (
            ("manifest.json", prepared["manifest"]),
            ("practice.json", {k: v for k, v in task.items() if k != "answer_key"}),
            ("instructor.answer-key.json", task["answer_key"]),
        ):
            path = check_path(directory / filename)
            if path.exists() and json.loads(path.read_text(encoding="utf-8")) != value:
                raise JournalConflict("Prepared artifact differs from its immutable event")
            if not path.exists():
                atomic_json(path, value)
        item = self.state()["queue"][prepared["queue_id"]]
        template_path = check_path(directory / "result-template.json")
        if not template_path.exists():
            template = dict(schema_version="1.0", result_id=None, queue_id=prepared["queue_id"],
                manifest_id=prepared["manifest_id"], practice_id=prepared["practice_id"],
                subject=item["subject"], concept=item["concept"], namespace=self.config.namespace,
                integration_test=self.config.namespace == "integration_tests",
                evidence_kind=item["training_type"], outcome="ungraded", grader="ungraded",
                questions_attempted=None, questions_correct=None, hints_used=None,
                independent=None, transfer=None, started_at=None, completed_at=None,
                grading_reason="", response_refs=[], weakness_tags=[], mistakes=[], open_questions=[])
            atomic_json(template_path, template)

    def start(self, queue_id, *, confirm=False):
        if not confirm:
            raise ValueError("Starting training requires explicit human confirmation")
        def change():
            item = self.state()["queue"][queue_id]
            if item["status"] == "in_progress":
                return {"status": "in_progress"}
            self._status(item, "in_progress", "Human explicitly started the training")
            return {"status": "in_progress"}
        return self._mutate(change)

    def cancel(self, queue_id):
        return self._mutate(lambda: self._status(self.state()["queue"][queue_id], "cancelled", "User cancelled"))

    def retry(self, queue_id):
        return self._mutate(lambda: self._status(self.state()["queue"][queue_id], "queued", "User requested retry"))

    def ingest_result(self, path, *, confirm_human=False):
        with self.lock():
            document, sha = self._read_input(path)
            data = validate_result(document)
            if data["namespace"] != self.config.namespace or data["integration_test"] != (self.config.namespace == "integration_tests"):
                raise ValueError("Result namespace mismatch")
            if not confirm_human or data["grader"] != "human" or data["outcome"] == "ungraded":
                raise ValueError("Assessment is pending: actual human grading and confirmation required")
            def append():
                state = self.state()
                prior = state["results"].get(data["result_id"])
                if prior:
                    if prior != data:
                        raise JournalConflict("Conflicting result id")
                    return {"duplicate": True, "result_id": data["result_id"]}
                if any(r["practice_id"] == data["practice_id"] for r in state["results"].values()):
                    raise JournalConflict("Practice already has an accepted result")
                item = state["queue"][data["queue_id"]]
                prepared = state["practices"][data["queue_id"]]
                if item["status"] != "in_progress":
                    raise ValueError("Training has not been started by the learner")
                starts = [e for e in self.store.events() if e["kind"] == "queue_status"
                          and e["payload"]["queue_id"] == data["queue_id"] and e["payload"]["to"] == "in_progress"]
                if not starts or timestamp(data["started_at"]) < timestamp(starts[-1]["timestamp"]):
                    raise ValueError("Result predates the confirmed training start")
                previous = state["concepts"][item["concept_key"]]["last_practiced"]
                if previous and timestamp(data["completed_at"]) < timestamp(previous):
                    raise ValueError("Out-of-order practice result requires human review")
                if (data["manifest_id"] != prepared["manifest_id"] or data["practice_id"] != prepared["practice_id"]
                        or data["concept"] != item["concept"] or data["subject"] != item["subject"]
                        or data["evidence_kind"] != item["training_type"]):
                    raise ValueError("Result does not match assigned training")
                self.store.append("practice", data["result_id"], data, at=data["completed_at"],
                                  source=prepared["practice_id"], raw_sha=sha)
                self.store.append("assessment", data["result_id"], data, at=data["completed_at"],
                                  source="human:" + data["result_id"], raw_sha=sha)
                self._status(item, "completed", "Learner response and human assessment recorded")
                return {"duplicate": False, "result_id": data["result_id"]}
            result = self._mutate(append)
            self.refresh_queue()
            return result

    def rebuild_state(self):
        with self.lock():
            recovery = check_path(self.config.root / "recovery")
            recovery.mkdir(exist_ok=True)
            if self.cache.exists():
                old = self.cache.read_bytes()
                backup = recovery / ("derived-" + hashlib.sha256(old).hexdigest() + ".json")
                if not backup.exists():
                    backup.write_bytes(old)
            candidate = self.state(check_cache=False)
            atomic_json(recovery / "candidate.json", candidate)
            # Current cache must equal a verified journal prefix, not arbitrary edited state.
            self.state()
            atomic_json(self.cache, candidate)
            return {"replayed_events": candidate["seq"], "comparison": "verified-prefix", "replaced": True}

    def explain(self, concept, *, subject=None):
        with self.lock():
            state = self.state()
            found = [v for v in state["concepts"].values()
                     if v["concept"] == concept and (subject is None or v["subject"] == subject)]
            if len(found) != 1:
                raise ValueError("Concept not found or ambiguous; specify subject")
            item = found[0]
            return {**item, "next_training": [q for q in state["queue"].values()
                    if q["concept_key"] == concept_key(item["subject"], concept)
                    and q["status"] in {"queued", "ready", "in_progress"}]}

    def project(self):
        from .views import project
        with self.lock():
            state = self.state()
            if not state["sessions"] and not state["results"]:
                return {"views": 0, "written": 0}
            return project(self.config, state)

    def publish(self, *, dry_run=False):
        with self.lock():
            state = self.state()
            if self.config.namespace == "learner" and self.config.binding is None:
                raise ValueError("Learner publishing requires the existing verified Reader binding")
            if not dry_run and not state["sessions"] and not state["results"]:
                return {"written": 0, "reason": "No automation evidence; existing Reader retained"}
            if not dry_run:
                self.project()
            # No rewritten transport, no alternate mobile target.
            return export_mobile(self.config.vault, self.config.reader, self.config.export_state,
                dry_run=dry_run, icloud_safe=self.config.binding is not None,
                icloud_binding=self.config.binding, automation_views=True)

    def cycle(self, *, day=None, publish=True):
        with self.lock():
            inbox = check_path(self.config.root / "pending-intake")
            inbox.mkdir(exist_ok=True)
            accepted, rejected = [], []
            for path in sorted(inbox.iterdir()):
                if path.suffix.lower() not in {".json", ".md"} or not path.is_file():
                    continue
                try:
                    accepted.append(self.intake(path))
                except (ValueError, KeyError) as exc:
                    rejected.append({"file": path.name, "error": type(exc).__name__})
            self.refresh_queue(day=day)
            projection = self.project()
            publication = self.publish() if publish else {"not_requested": True}
            return {"accepted": accepted, "rejected": rejected, "projection": projection,
                    "publish": publication, "training_started": False}
