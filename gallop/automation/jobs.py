"""Durable DeepTutor submission. A caller deadline never kills or forgets a job."""
from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gallop.adapters.deeptutor import DeepTutorAdapter
from gallop.core.io import atomic_json, identifier
from gallop.mobile import check_path
from .protocol import digest


@contextmanager
def file_lock(path):
    """OS releases the lock on crash; keep its inode/file stable between callers."""
    path = check_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if not path.stat().st_size:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def process_identity(pid):
    """PID plus birth time prevents confusing a reused PID with our worker."""
    if os.name == 'nt':
        from ctypes import wintypes
        k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        h = k.OpenProcess(0x1000, False, pid)
        if not h:
            if ctypes.get_last_error() == 87:
                return None
            raise OSError('Cannot establish process identity safely')
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            code = wintypes.DWORD()
            if not k.GetProcessTimes(h, *(ctypes.byref(t) for t in times)) or not k.GetExitCodeProcess(h, ctypes.byref(code)):
                raise OSError('Cannot read process lifetime')
            if code.value != 259:
                return None
            return [pid, (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime]
        finally:
            k.CloseHandle(h)
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return None if fields[0] == 'Z' else [pid, fields[19]]
    except FileNotFoundError:
        return None


def alive(identity):
    return bool(identity) and process_identity(identity[0]) == identity


def read(path):
    return json.loads(check_path(path).read_text(encoding='utf-8'))


class Jobs:
    def __init__(self, root):
        self.root = check_path(root / 'jobs')

    def directory(self, job_id):
        return check_path(self.root / identifier(job_id))

    def prepare(self, queue_id, manifest, adapter):
        job_id = 'job-' + digest([queue_id, manifest['manifest_id']])[:24]
        directory = self.directory(job_id)
        directory.mkdir(parents=True, exist_ok=True)
        request = dict(job_id=job_id, queue_id=queue_id, manifest=manifest,
                       executable=str(adapter.executable), home=str(adapter.home) if adapter.home else None)
        with file_lock(directory / '.lock'):
            path = directory / 'request.json'
            if path.exists() and read(path) != request:
                raise ValueError('Job identity conflicts with immutable manifest or runtime')
            if not path.exists():
                atomic_json(path, request)
        return job_id

    def submit(self, job_id, *, retry=False, deadline=240):
        if deadline <= 0:
            raise ValueError('Deadline must be positive')
        directory = self.directory(job_id)
        with file_lock(directory / '.lock'):
            status = self.poll(job_id)
            if status['status'] != 'prepared':
                if not retry:
                    return status
                if status['status'] != 'failed' or not status.get('retry_safe'):
                    raise ValueError('Retry refused: collect existing/late result or resolve uncertain process first')
            attempt = status.get('attempt', 0) + 1
            run = directory / f'attempt-{attempt:04d}'
            run.mkdir()
            # Commit submission before launching. An uncertain spawn is never auto-resubmitted.
            atomic_json(run / 'submitted.json', dict(at=time.time(), deadline=deadline, attempt=attempt))
            env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
            env['PYTHONPATH'] = str(Path(__file__).resolve().parents[2])
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            try:
                with (run / 'worker.log').open('wb') as log:
                    p = subprocess.Popen([sys.executable, '-B', '-m', 'gallop.automation.jobs', str(run)],
                        env=env, cwd=Path(__file__).resolve().parents[2], stdin=subprocess.DEVNULL,
                        stdout=log, stderr=log, creationflags=flags, close_fds=True)
                atomic_json(run / 'launcher.json', dict(identity=process_identity(p.pid)))
            except OSError:
                # Popen itself could have succeeded before a subsequent persistence error.
                # Leave an uncertain submission recoverable, never mark it safe to retry.
                raise
        return self.poll(job_id)

    def poll(self, job_id):
        directory = self.directory(job_id)
        request = read(directory / 'request.json')
        runs = sorted(directory.glob('attempt-*'))
        base = dict(job_id=job_id, queue_id=request['queue_id'], manifest_id=request['manifest']['manifest_id'])
        if not runs:
            return dict(base, status='prepared', attempt=0)
        run = check_path(runs[-1])
        submitted = read(run / 'submitted.json')
        elapsed = max(0, time.time() - submitted['at'])
        base.update(attempt=submitted['attempt'], elapsed_seconds=round(elapsed, 3))
        if (run / 'completed.json').exists():
            completion = read(run / 'completed.json')
            if completion.get('job_id') != job_id or completion.get('manifest_id') != base['manifest_id']:
                raise ValueError('Completion identity mismatch')
            return dict(base, status='completed', completion=completion, late=completion['at'] > submitted['at'] + submitted['deadline'])
        if (run / 'exit.json').exists():
            exit_info = read(run / 'exit.json')
            return dict(base, status='failed', reason=exit_info['reason'], retry_safe=exit_info['retry_safe'])
        active = False
        for name in ('launcher.json', 'worker.json', 'provider.json'):
            if (run / name).exists():
                active = alive(read(run / name)['identity']) or active
        # Collect a fully serialized correlated result even if the worker died after generation.
        if (run / 'stdout.ndjson').exists():
            completion = recover_output(request, run)
            if completion:
                return dict(base, status='completed', completion=completion, late=elapsed > submitted['deadline'])
        provider_known = (run / 'provider.json').exists()
        if not active and provider_known:
            return dict(base, status='failed', reason='process_exited_without_result', retry_safe=True)
        status = 'running' if (run / 'provider.json').exists() else 'submitted'
        if elapsed > submitted['deadline']:
            return dict(base, status='timed_out', timeout_reason='caller_deadline_exceeded; job and output retained',
                        process_active=active, retry_safe=False)
        return dict(base, status=status, process_active=active)


def recover_output(request, run):
    output = (run / 'stdout.ndjson').read_text(encoding='utf-8', errors='replace')
    events = []
    for line in output.splitlines():
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        except json.JSONDecodeError:
            continue
    sessions = [e for e in events if e.get('type') == 'session' and e.get('turn_id')]
    if not sessions:
        return None
    turn_id = sessions[0]['turn_id']
    final = [e for e in events if e.get('type') == 'result' and e.get('source') == 'deep_question' and e.get('turn_id') == turn_id]
    done = any(e.get('type') == 'done' and e.get('turn_id') == turn_id and e.get('metadata', {}).get('status') == 'completed' for e in events)
    if not final or not done:
        return None
    adapter = DeepTutorAdapter(Path(request['executable']))
    try:
        practice = adapter.decode(request['manifest'], json.dumps(final[-1]))
    except ValueError:
        return None
    practice['practice_id'] = 'provider-' + request['job_id']
    return dict(job_id=request['job_id'], manifest_id=request['manifest']['manifest_id'],
                turn_id=turn_id, session_id=sessions[0].get('session_id'), at=final[-1]['timestamp'],
                output_sha256=hashlib.sha256(output.encode()).hexdigest(), practice=practice)


def worker(run):
    run = check_path(run)
    request = read(run.parent / 'request.json')
    # A permanent claim prevents an accidentally launched second worker for this attempt.
    with (run / 'claimed').open('x'):
        pass
    atomic_json(run / 'worker.json', dict(identity=process_identity(os.getpid()), at=time.time()))
    adapter = DeepTutorAdapter(Path(request['executable']), home=Path(request['home']) if request['home'] else None)
    command, env = adapter.request(request['manifest'])
    env.update(PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
    with (run / 'stdout.ndjson').open('wb') as out, (run / 'stderr.log').open('wb') as err:
        try:
            p = subprocess.Popen(command, cwd=adapter.home, env=env, stdin=subprocess.DEVNULL,
                                 stdout=out, stderr=err, shell=False,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except OSError:
            atomic_json(run / 'exit.json', dict(reason='process_start_failed', retry_safe=True))
            return
        atomic_json(run / 'provider.json', dict(identity=process_identity(p.pid), at=time.time()))
        rc = p.wait()
    completion = recover_output(request, run)
    if completion:
        atomic_json(run / 'completed.json', completion)
    reason = 'completed' if completion else ('no_usable_result' if rc == 0 else f'provider_exit_{rc}')
    atomic_json(run / 'exit.json', dict(reason=reason,
                                      retry_safe=True, at=time.time(), returncode=rc))


if __name__ == '__main__':
    worker(Path(sys.argv[1]))
