"""A minimal Redis-backed queue implementation for demo and tests."""
from __future__ import annotations

import base64
import importlib
import pickle
import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, Optional


class SimpleJob:
    def __init__(
        self,
        func_or_path,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        description: Optional[str],
        *,
        job_id: Optional[str] = None,
        enqueued_at: Optional[float] = None,
    ):
        if callable(func_or_path):
            func = func_or_path
            self.func_path = f"{func.__module__}:{func.__qualname__}"
            self._func = func
        else:
            self.func_path = str(func_or_path)
            self._func = None
        self.id = job_id or uuid.uuid4().hex
        self.args = args
        self.kwargs = kwargs
        self.description = description
        self.enqueued_at = enqueued_at or time.time()
        self._result: Any = None

    @property
    def func_name(self) -> str:
        return self.func_path.replace(":", ".")

    def perform(self) -> Any:
        func = self._func or self._resolve_func()
        self._result = func(*self.args, **self.kwargs)
        return self._result

    def _resolve_func(self):
        module_name, qualname = self.func_path.split(":", 1)
        module = importlib.import_module(module_name)
        attr = module
        for part in qualname.split('.'):
            if part == '<locals>':
                continue
            attr = getattr(attr, part)
        self._func = attr
        return attr

    def serialize(self) -> str:
        payload = {
            'id': self.id,
            'func_path': self.func_path,
            'args': self.args,
            'kwargs': self.kwargs,
            'description': self.description,
            'enqueued_at': self.enqueued_at,
        }
        return base64.b64encode(pickle.dumps(payload)).decode('ascii')

    @classmethod
    def deserialize(cls, data: str) -> "SimpleJob":
        payload = pickle.loads(base64.b64decode(data.encode('ascii')))
        args = payload['args']
        if not isinstance(args, tuple):
            args = tuple(args)
        kwargs = payload['kwargs']
        if not isinstance(kwargs, dict):
            kwargs = dict(kwargs)
        return cls(
            payload['func_path'],
            args,
            kwargs,
            payload['description'],
            job_id=payload['id'],
            enqueued_at=payload['enqueued_at'],
        )


class SimpleQueue:
    def __init__(self, name: str = "default", connection: Any = None):
        self.name = name
        self.connection = connection
        self._jobs: Dict[str, SimpleJob] = {}
        self._pending: Deque[str] = deque()

    def enqueue(self, func, *args, description: Optional[str] = None, **kwargs) -> SimpleJob:
        job = SimpleJob(func, args, kwargs, description)
        self._jobs[job.id] = job
        if self.connection:
            self._persist_job(job)
        else:
            self._pending.append(job.id)
        return job

    def fetch_job(self, job_id: str) -> Optional[SimpleJob]:
        job = self._jobs.get(job_id)
        if job:
            return job
        if not self.connection:
            return None
        data = self.connection.get(self._job_key(job_id))
        if not data:
            return None
        job = SimpleJob.deserialize(data)
        self._jobs[job.id] = job
        return job

    def pop_job(self) -> Optional[SimpleJob]:
        job_id: Optional[str]
        if self.connection:
            job_id = self.connection.lpop(self._pending_key())
        else:
            if not self._pending:
                return None
            job_id = self._pending.popleft()
        if not job_id:
            return None
        return self.fetch_job(job_id)

    def _job_key(self, job_id: str) -> str:
        return f"rq:job:{self.name}:{job_id}"

    def _pending_key(self) -> str:
        return f"rq:queue:{self.name}"

    def _persist_job(self, job: SimpleJob) -> None:
        payload = job.serialize()
        self.connection.set(self._job_key(job.id), payload)
        self.connection.rpush(self._pending_key(), job.id)


class SimpleWorker:
    def __init__(self, queue: SimpleQueue, sleep: float = 1.0):
        self.queue = queue
        self.sleep = sleep

    def work(self, burst: bool = False) -> None:
        while True:
            job = self.queue.pop_job()
            if job:
                job.perform()
                continue
            if burst:
                break
            time.sleep(self.sleep)
