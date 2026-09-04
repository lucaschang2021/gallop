"""Deterministic evidence reducer and explicit mastery safety rules, version 1."""
from copy import deepcopy
from datetime import date, timedelta
import json
from importlib.resources import files

from .protocol import concept_names, digest, timestamp
from .store import JournalConflict

POLICIES = json.loads(files("gallop.schemas").joinpath("training-policies.json").read_text(encoding="utf-8"))


def concept_key(subject, concept):
    return digest([subject, concept])[:24]


def blank(subject, concept):
    return dict(subject=subject, concept=concept, mastery_level=0, confidence="low",
                evidence_count=0, last_seen=None, last_practiced=None, mistake_count=0,
                success_count=0, weakness_tags=[], open_questions=[], evidence_refs=[],
                successes=[], mistakes=[], history=[], observations=[])


def union(left, right):
    seen = {digest(v) for v in left}
    for value in right:
        if digest(value) not in seen:
            left.append(deepcopy(value))
            seen.add(digest(value))


def mastery_gate(current, successes, outcome):
    """Failure adds weakness without erasing mastery; promotions require durable evidence."""
    if outcome != "pass":
        return current, "Failure or ungraded work does not erase mastery"
    independent = [e for e in successes if e["independent"] and e["hints_used"] == 0]
    days = {timestamp(e["at"]).date() for e in independent}
    kinds = {e["kind"] for e in independent}
    cap = 0
    if len(days) >= 2:
        cap = 2
    if len(days) >= 3 and len(kinds) >= 2:
        cap = 3
    if len(days) >= 4 and len(kinds) >= 3:
        cap = 4
    delayed = len(days) >= 2 and (max(days) - min(days)).days >= 30
    if (len(days) >= 5 and len(kinds) >= 3 and delayed
            and "oral_exam" in kinds and any(e["transfer"] for e in independent)):
        cap = 5
    new = max(current, min(current + 1, cap))
    return new, ("Independent evidence across distinct days and task types supports one level"
                 if new > current else "Insufficient diverse, delayed, independent evidence for promotion")


def replay(events, *, verify=True):
    state = {"version": 1, "seq": 0, "head": "", "concepts": {}, "sessions": {},
             "queue": {}, "practices": {}, "results": {}, "transitions": []}
    seen_transitions = []
    seen_readiness = []

    def update(event, subject, name, action):
        key = concept_key(subject, name)
        item = state["concepts"].setdefault(key, blank(subject, name))
        before = deepcopy(item)
        reason = action(item)
        item["evidence_count"] += 1
        item["evidence_refs"].append(event["event_id"])
        if not item["last_seen"] or timestamp(event["timestamp"]) > timestamp(item["last_seen"]):
            item["last_seen"] = event["timestamp"]
        transition = dict(concept_key=key, source_event=event["event_id"],
                          before=before["mastery_level"], after=item["mastery_level"],
                          confidence=item["confidence"], reason=reason,
                          evidence_refs=list(item["evidence_refs"]))
        item["history"].append(transition)
        state["transitions"].append(transition)

    for event in events:
        kind, data = event["kind"], event["payload"]
        if kind == "session":
            state["sessions"][event["event_id"]] = data
            names = concept_names(data)
            for name in names:
                def exposure(item):
                    union(item["weakness_tags"], data["weakness_tags"])
                    union(item["open_questions"], data["open_questions"])
                    relevant = [m for m in data["mistakes"] if len(names) == 1 or
                                isinstance(m, dict) and m.get("concept") == name]
                    item["mistake_count"] += len(relevant)
                    union(item["mistakes"], [{"source": event["event_id"], "detail": m} for m in relevant])
                    item["observations"].append({"source": event["event_id"], "kind": "course_exposure",
                                                 "at": event["timestamp"]})
                    return "Course exposure records context, never a mastery score or completed assessment"
                update(event, data["tutor"], name, exposure)
        elif kind == "practice":
            state["results"][data["result_id"]] = data
            def attempt(item):
                if not item["last_practiced"] or timestamp(data["completed_at"]) > timestamp(item["last_practiced"]):
                    item["last_practiced"] = data["completed_at"]
                item["observations"].append({"source": event["event_id"], "kind": "practice_attempt"})
                return "Learner attempt recorded; grading is a separate confirmed assessment"
            update(event, data["subject"], data["concept"], attempt)
        elif kind == "assessment":
            def assessment(item):
                if data.get("elite_evidence"):
                    return "Explicit Elite evidence owns performance credit; legacy envelope is provenance only"
                outcome = data["outcome"]
                union(item["weakness_tags"], data["weakness_tags"])
                union(item["open_questions"], data["open_questions"])
                if outcome == "pass":
                    item["success_count"] += 1
                    item["successes"].append(dict(at=data["completed_at"], kind=data["evidence_kind"],
                        independent=data["independent"], hints_used=data["hints_used"],
                        transfer=data["transfer"], ref=event["event_id"]))
                elif outcome == "fail":
                    item["mistake_count"] += max(1, len(data["mistakes"]))
                    union(item["weakness_tags"], [data["evidence_kind"] + "-failure"])
                    union(item["mistakes"], [{"source": event["event_id"], "detail": m}
                                            for m in data["mistakes"]] or
                          [{"source": event["event_id"], "detail": "Confirmed unsuccessful attempt"}])
                item["mastery_level"], reason = mastery_gate(item["mastery_level"], item["successes"], outcome)
                independent = [s for s in item["successes"] if s["independent"] and not s["hints_used"]]
                days = {timestamp(s["at"]).date() for s in independent}
                item["confidence"] = ("high" if len(days) >= 4 and len({s["kind"] for s in independent}) >= 3
                                      else "medium" if len(days) >= 2 else "low")
                if outcome == "fail":
                    item["confidence"] = "low"
                return reason + "; " + data["grading_reason"]
            update(event, data["subject"], data["concept"], assessment)
        elif kind == "queue_created":
            if data["queue_id"] in state["queue"]:
                raise JournalConflict("Duplicate queue creation")
            state["queue"][data["queue_id"]] = deepcopy(data)
        elif kind == "queue_status":
            item = state["queue"][data["queue_id"]]
            if item["status"] != data["from"]:
                raise JournalConflict("Invalid queued state transition")
            item["status"] = data["to"]
            item["status_reason"] = data["reason"]
        elif kind == "prepared":
            state["practices"][data["queue_id"]] = data
        elif kind in {"elite_evidence", "benchmark", "prerequisite_link", "target_capability"}:
            from .elite_state import apply
            apply(state, event, update)
        elif kind == "readiness_transition":
            if data not in state.get("elite", {}).get("readiness_transitions", []) or data in seen_readiness:
                raise JournalConflict("Readiness transition does not match replayed evidence")
            seen_readiness.append(data)
        elif kind == "state_transition":
            if data not in state["transitions"] or data in seen_transitions:
                raise JournalConflict("State transition does not match replayed evidence")
            seen_transitions.append(data)
        else:
            raise JournalConflict("Unknown event kind")
        state["seq"], state["head"] = event["seq"], event["hash"]
    if verify and len(seen_transitions) != len(state["transitions"]):
        raise JournalConflict("Missing state transition audit events")
    if verify and len(seen_readiness) != len(state.get("elite", {}).get("readiness_transitions", [])):
        raise JournalConflict("Missing readiness transition audit events")
    return state


def training_candidate(item, day, completed_reviews=()):
    policy = POLICIES[item["subject"]]
    tags = set(item["weakness_tags"])
    # Preserve the tutor protocol's per-session T+1/T+7/T+30 dates.
    # Unrelated later practice must not reset an already scheduled review.
    exposures = [e for e in item["observations"] if e["kind"] == "course_exposure"]
    if not exposures and item["last_seen"]:
        exposures = [{"at": item["last_seen"], "source": item["evidence_refs"][0]}]
    scheduled = sorted(
        (date.fromisoformat(e["at"][:10]) + timedelta(days=offset), e["source"], offset)
        for e in exposures for offset in (1, 7, 30))
    due = next(((when, source, offset) for when, source, offset in scheduled
                if when <= day and digest([source, offset]) not in completed_reviews), None)
    review_key = digest([due[1], due[2]]) if due else None
    if tags & {"severe", "prerequisite-failure", "prerequisite_failure"}:
        priority, reason = 0, "Severe weakness or prerequisite failure"
    elif item["mistake_count"] >= 2 or tags & {"oral_exam-failure", "hard_problem-failure"}:
        priority, reason = 1, "Repeated mistakes or failed demanding assessment"
    elif item["confidence"] == "low":
        priority, reason = 2, "Low confidence requires more independent evidence"
    elif due:
        priority, reason = 3, f"Session review T+{due[2]} due {due[0].isoformat()}"
    else:
        priority, reason = 4, "Extension after recent evidence"
    mode = "review" if priority == 3 else policy["training_types"][item["success_count"] % len(policy["training_types"])]
    key = concept_key(item["subject"], item["concept"])
    return dict(queue_id="q-" + digest([key, item["evidence_refs"], mode, review_key if priority == 3 else None])[:24],
                subject=item["subject"], concept=item["concept"], training_type=mode,
                focus=policy["focus"], priority="P" + str(priority), reason=reason,
                evidence_refs=item["evidence_refs"], created_at=day.isoformat(),
                status="queued", due_review=bool(due), review_key=review_key if priority == 3 else None,
                concept_key=key)
