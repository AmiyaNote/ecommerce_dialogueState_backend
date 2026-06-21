from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageType(Enum):
    TEXT = "text"  # 文本类型
    OBJECT = "object"  # 对象类型


class FocusedObject(BaseModel):
    type: str
    id: str
    title: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class UserMessage(BaseModel):
    sender_id: str
    message_id: str
    type: MessageType
    text: str
    object: FocusedObject | None = None


class BotMessage(BaseModel):
    text: str
    object: FocusedObject | None = None


class ProcessResult(BaseModel):
    sender_id: str
    message_id: str
    messages: list[BotMessage]
