import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from domain.context import AnySystemContext, TaskContext
from domain.message import FocusedObject, UserMessage
from domain.session import Session
from domain.turn import Turn


class DialogueState(BaseModel):
    """Dialogue runtime state.
    `@dataclass`：标准库的数据容器，自动生成 `__init__ / __repr__ / __eq__`，轻量，适合纯内部对象。
    `BaseModel`：Pydantic 数据模型，除字段定义外，还提供类型校验、`model_dump()` 序列化、`model_validate()` 反序列化。
    `dataclass` 不会自动递归把嵌套 dict 还原成对象，复杂嵌套通常要手写 `to_dict/from_dict`。
    `BaseModel` 会基于类型声明递归处理嵌套模型，更适合 JSON、API、数据库状态存储。
    本项目的 `DialogueState -> Session -> Turn -> Message` 嵌套较深且需要持久化恢复。
    因此选 `BaseModel`，能减少重复代码，并和 FastAPI/Pydantic 技术栈保持一致。
    """

    sender_id: str
    active_task: TaskContext | None = None
    paused_tasks: list[TaskContext] = Field(default_factory=list)
    active_system_task: AnySystemContext | None = None
    focused_object: FocusedObject | None = None
    sessions: list[Session] = Field(default_factory=list)
    current_session_id: str | None = None
    pending_turn: Turn | None = None

    # =======task========
    def start_task(self, task_context: TaskContext):
        self.active_task = task_context

    def end_active_task(self):
        self.active_task = None

    def cancel_active_task(self):
        self.active_task = None
        self.active_system_task = None

    def interrupt_active_task(self):
        if self.active_task is not None:
            self.paused_tasks.append(self.active_task)
        self.active_task = None

    def resume_task(self, flow_id: str):
        for task in self.paused_tasks:
            if task.flow_id == flow_id:
                self.active_task = task
                self.paused_tasks.remove(task)
                break

    # sys task
    def start_system_task(self, system_context: AnySystemContext):
        self.active_system_task = system_context

    def end_system_task(self):
        self.active_system_task = None

    def current_task(self):
        return self.active_system_task or self.active_task

    # ==========slot=========
    def set_slots(self, slots: dict[str, Any]):
        if self.active_task is None:
            return
        self.active_task.slots.update(slots)

    def remove_slot(self, slot_name: str):
        if self.active_task is None:
            return
        self.active_task.slots.pop(slot_name)

    # =======session==========
    def start_session(self):
        now = time.time()
        session = Session(
            session_id=str(uuid.uuid4()),
            started_at=now,
            last_activity_at=now,
        )
        self.sessions.append(session)
        self.current_session_id = session.session_id

    def current_session(self) -> Session | None:
        for session in self.sessions:
            if session.session_id == self.current_session_id:
                return session
        return None

    def close_current_session(self):
        session = self.current_session()
        if session is None:
            return
        session.closed_at = time.time()
        self.current_session_id = None

    def reset_runtime_state_for_new_session(self):
        self.active_task = None
        self.active_system_task = None
        self.focused_object = None
        self.paused_tasks = []

    # ========turn=========
    def begin_turn(self, message: UserMessage):
        self.pending_turn = Turn(
            turn_id=str(uuid.uuid4()),
            user_message=message,
        )

    def commit_pending_turn(self):
        session = self.current_session()
        if session is None or self.pending_turn is None:
            return
        session.turns.append(self.pending_turn)
        self.pending_turn = None

    # focus_object
    def set_focused_object(self, object: FocusedObject):
        self.focused_object = object
