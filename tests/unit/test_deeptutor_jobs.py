"""Offline fault tests are separate from the required online acceptance evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from gallop.adapters.deeptutor import DeepTutorAdapter
from gallop.automation.jobs import Jobs, alive, file_lock, process_identity, worker
from gallop.core.io import atomic_json
from test_automation import app, accept


def job(app, monkeypatch, *, deadline=240):
    accept(app)
    q = next(q for q in app.queue() if q['status'] == 'queued')
    pending = app.prepare(q['queue_id'], question_count=1, _defer=True)
    jobs = Jobs(app.config.root)
    jid = jobs.prepare(q['queue_id'], pending['manifest'], DeepTutorAdapter(Path(sys.executable)))
    run = jobs.directory(jid) / 'attempt-0001'
    run.mkdir()
    atomic_json(run / 'submitted.json', dict(at=time.time(), deadline=deadline, attempt=1))
    atomic_json(run / 'worker.json', dict(identity=process_identity(os.getpid())))
    atomic_json(run / 'provider.json', dict(identity=process_identity(os.getpid())))
    return jobs, jid, run, q


def output(run, *, wrong_turn=False, done=True, count=1):
    events = [dict(type='session', turn_id='turn-one', session_id='test-session'),
              dict(type='result', turn_id='wrong' if wrong_turn else 'turn-one', source='deep_question',
                   timestamp=time.time(), metadata=dict(summary=dict(success=True, results=[
                       dict(qa_pair=dict(question='Test 2+2?', options={'A':'4'}, correct_answer='A')) for _ in range(count)])))]
    if done:
        events.append(dict(type='done', turn_id='turn-one', metadata=dict(status='completed')))
    (run / 'stdout.ndjson').write_text('\n'.join(json.dumps(e) for e in events), encoding='utf-8')


def test_running_deadline_and_late_collection_survive_new_service(app, monkeypatch):
    jobs, jid, run, q = job(app, monkeypatch)
    assert jobs.poll(jid)['status'] == 'running'
    submitted = json.loads((run / 'submitted.json').read_text())
    submitted['at'] -= 300
    atomic_json(run / 'submitted.json', submitted)
    assert Jobs(app.config.root).poll(jid)['status'] == 'timed_out'
    with pytest.raises(ValueError, match='Retry refused'):
        jobs.submit(jid, retry=True)
    output(run)
    assert jobs.poll(jid)['status'] == 'completed' and jobs.poll(jid)['late']
    assert not app.collect(jid)['duplicate']
    before = app.state()
    assert app.collect(jid)['duplicate']
    assert app.state() == before
    assert before['queue'][q['queue_id']]['status'] == 'ready'
    assert not before['results'] and next(iter(before['concepts'].values()))['mastery_level'] == 0


@pytest.mark.parametrize('options', [dict(wrong_turn=True), dict(done=False), dict(count=2)])
def test_reject_uncorrelated_partial_or_wrong_count(app, monkeypatch, options):
    jobs, jid, run, _ = job(app, monkeypatch)
    output(run, **options)
    assert jobs.poll(jid)['status'] == 'running'
    assert app.collect(jid)['status'] == 'running'
    assert not app.state()['practices']


def test_duplicate_submission_and_manifest_conflict(app, monkeypatch):
    jobs, jid, run, q = job(app, monkeypatch)
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **kw: pytest.fail('must not spawn duplicate'))
    assert jobs.submit(jid)['status'] == 'running'
    request = json.loads((run.parent / 'request.json').read_text())
    manifest = request['manifest']; manifest['topic'] = 'conflicting topic'
    with pytest.raises(ValueError, match='conflicts'):
        jobs.prepare(q['queue_id'], manifest, DeepTutorAdapter(Path(sys.executable)))


def test_crashed_worker_recovers_serialized_result(app, monkeypatch):
    jobs, jid, run, _ = job(app, monkeypatch)
    monkeypatch.setattr('gallop.automation.jobs.alive', lambda identity: False)
    output(run)
    assert Jobs(app.config.root).poll(jid)['status'] == 'completed'
    assert app.collect(jid)['status'] == 'completed'


def test_crashed_worker_without_result_and_retry_preserves_attempt(app, monkeypatch):
    jobs, jid, run, _ = job(app, monkeypatch)
    monkeypatch.setattr('gallop.automation.jobs.alive', lambda identity: False)
    assert jobs.poll(jid)['status'] == 'failed'
    class Dummy:
        pid = os.getpid()
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **kw: Dummy())
    assert jobs.submit(jid, retry=True)['attempt'] == 2
    assert run.is_dir() and (run / 'submitted.json').exists()


def test_uncertain_spawn_never_blindly_retries(app, monkeypatch):
    jobs, jid, run, _ = job(app, monkeypatch, deadline=0.001)
    (run / 'provider.json').unlink(); (run / 'worker.json').unlink()
    with pytest.raises(ValueError, match='Retry refused'):
        jobs.submit(jid, retry=True)


def test_pid_reuse_is_not_live():
    identity = process_identity(os.getpid())
    assert alive(identity)
    assert not alive([identity[0], str(identity[1]) + '-different-birth'])


def test_os_lock_released_after_process_crash(tmp_path):
    path = tmp_path / 'writer.lock'
    code = 'import os,sys; from pathlib import Path; from gallop.automation.jobs import file_lock; ctx=file_lock(Path(sys.argv[1]));ctx.__enter__();os._exit(3)'
    result = subprocess.run([sys.executable, '-B', '-c', code, str(path)], capture_output=True)
    assert result.returncode == 3
    with file_lock(path):
        with pytest.raises(OSError):
            with file_lock(path):
                pytest.fail('second writer acquired lock')


def test_worker_real_subprocess_serialization_and_instructor_answer_separation(app, monkeypatch):
    jobs, jid, run, q = job(app, monkeypatch)
    output(run)
    body = (run / 'stdout.ndjson').read_text()
    monkeypatch.setattr(DeepTutorAdapter, 'request', lambda self, m: (
        [sys.executable, '-B', '-c', 'print(' + repr(body) + ')'], dict(os.environ)))
    worker(run)
    status = jobs.poll(jid)
    assert status['status'] == 'completed'
    assert status['completion']['practice']['answer_key'][0]['correct_answer'] == 'A'
    app.collect(jid)
    public = json.loads((app.config.root / 'prepared' / q['queue_id'] / 'practice.json').read_text())
    assert 'answer_key' not in public and 'correct_answer' not in json.dumps(public)


def test_collection_recovers_after_journal_commit_before_cache_write(app, monkeypatch):
    jobs, jid, run, q = job(app, monkeypatch)
    output(run)
    import gallop.automation.service as service
    original = service.atomic_json
    def fail_cache(path, value):
        if path.name == 'derived-state.json':
            raise OSError('simulated crash after journal commit')
        return original(path, value)
    monkeypatch.setattr(service, 'atomic_json', fail_cache)
    with pytest.raises(OSError):
        app.collect(jid)
    monkeypatch.setattr(service, 'atomic_json', original)
    assert app.collect(jid)['duplicate']
    app.rebuild_state()
    assert sum(e['kind'] == 'prepared' for e in app.store.events()) == 1
    assert app.state()['queue'][q['queue_id']]['status'] == 'ready'


def test_late_result_cannot_revive_cancelled_queue(app, monkeypatch):
    jobs, jid, run, q = job(app, monkeypatch)
    app.cancel(q['queue_id'])
    output(run)
    with pytest.raises(ValueError, match='Only queued'):
        app.collect(jid)
    assert jobs.poll(jid)['status'] == 'completed'
    assert app.state()['queue'][q['queue_id']]['status'] == 'cancelled'


def test_completion_manifest_mismatch_is_rejected(app, monkeypatch):
    jobs, jid, run, _ = job(app, monkeypatch)
    atomic_json(run / 'completed.json', dict(job_id=jid, manifest_id='wrong'))
    with pytest.raises(ValueError, match='identity mismatch'):
        app.collect(jid)
