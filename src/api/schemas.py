import uuid

from pydantic import BaseModel

from domain.message import UserMessage, MessageType, FocusedObject, ProcessResult


# ChatObject,ChatRequest,
# ChatBotMessage / ChatResponse,
# HistoryMessage / HistoryResponse

# =====接收
class ChatObject(BaseModel):
    type: str
    id: str
    title: str
    attributes: dict


class ChatRequest(BaseModel):
    sender_id: str
    message_id: str
    text: str
    object: ChatObject
# ========返回
class ChatBotMessage(BaseModel):
    text: str | None = None
    object: ChatObject | None = None


class ChatResponse(BaseModel):
    sender_id: str
    message_id: str
    messages: list[ChatBotMessage]


# ========history
class HistoryMessage(BaseModel):
    role: str  # user or bot
    text: str | None = None
    object: ChatObject | None = None


class HistoryResponse(BaseModel):
    sender_id: str
    messages: list[HistoryMessage]




def _build_user_message(chat_request: ChatRequest) -> UserMessage:
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id=chat_request.message_id or str(uuid.uuid4()),
        type=MessageType.TEXT if chat_request.text else MessageType.OBJECT,
        text=chat_request.text,
        object=FocusedObject(
            type=chat_request.object.type,
            id=chat_request.object.id,
            title=chat_request.object.title,
            attributes=chat_request.object.attributes,
        ) if chat_request.object else None,
    )

def _build_chat_response(process_result: ProcessResult) -> ChatResponse:
    return ChatResponse(
        sender_id=process_result.sender_id,
        message_id=process_result.message_id,
        messages=[
            ChatBotMessage(
                text=message.text,
                object=ChatObject(
                    type=message.object.type,
                    id=message.object.id,
                    title=message.object.title,
                    attributes=message.object.attributes,
                ) if message.object else None,
            ) for message in process_result.messages
        ],
    )