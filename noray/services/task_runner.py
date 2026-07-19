"""
NORAY — Asynchronous Task Runner

A database-backed queue leveraging asyncio. Designed to be easily 
swapped for Celery/Temporal in future distributed phases.
"""

import asyncio
from typing import Dict, Any, Callable, Awaitable
from datetime import datetime
import uuid

class TaskState:
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_HITL = "awaiting_hitl"
    COMPLETED = "completed"
    FAILED = "failed"

class AsyncTaskRecord:
    def __init__(self, name: str, payload: Dict[str, Any]):
        self.task_id = str(uuid.uuid4())
        self.name = name
        self.payload = payload
        self.state = TaskState.PENDING
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error: str = None
        self.result: Any = None

class TaskRunner:
    def __init__(self):
        self._queue: asyncio.Queue[AsyncTaskRecord] = asyncio.Queue()
        self._tasks_db: Dict[str, AsyncTaskRecord] = {}
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Any]]] = {}
        self._workers: List[asyncio.Task] = []

    def register_handler(self, name: str, handler: Callable[[Dict[str, Any]], Awaitable[Any]]):
        self._handlers[name] = handler

    async def enqueue(self, name: str, payload: Dict[str, Any]) -> str:
        record = AsyncTaskRecord(name, payload)
        self._tasks_db[record.task_id] = record
        await self._queue.put(record)
        return record.task_id
        
    def get_status(self, task_id: str) -> AsyncTaskRecord:
        return self._tasks_db.get(task_id)

    async def _worker(self):
        while True:
            record = await self._queue.get()
            try:
                record.state = TaskState.RUNNING
                record.updated_at = datetime.utcnow()
                
                handler = self._handlers.get(record.name)
                if handler:
                    result = await handler(record.payload)
                    record.result = result
                    record.state = TaskState.COMPLETED
                else:
                    raise ValueError(f"No handler registered for {record.name}")
            except Exception as e:
                record.error = str(e)
                record.state = TaskState.FAILED
            finally:
                record.updated_at = datetime.utcnow()
                self._queue.task_done()

    def start_workers(self, concurrency: int = 3):
        for _ in range(concurrency):
            task = asyncio.create_task(self._worker())
            self._workers.append(task)
            
    async def stop_workers(self):
        await self._queue.join()
        for task in self._workers:
            task.cancel()
