from fastapi import APIRouter, Depends

from api.dependencies import get_dialogue_service
from api.schemas import ChatRequest, ChatResponse, _build_user_message, _build_chat_response, HistoryResponse, \
    HistoryMessage
from domain.message import ProcessResult
from service.dialogue_service import DialogueService

chat_router = APIRouter()





@chat_router.get("/api/chat")
async def chat(chat_request: ChatRequest,
               # 必须用 Depends，不能直接 import：DialogueService → Repository → AsyncSession，
               # 而 AsyncSession 必须每次请求独立创建、用完关闭，全局单例会导致事务串扰和连接池泄露。
               dialogue_service: DialogueService = Depends(get_dialogue_service)) -> ChatResponse:
    """
        1，dto转化为为ddd
        2.ddd 交由service处理
        3，ddd封装成 前端dto 响应
    """
    user_msg = _build_user_message(chat_request)

    process_result: ProcessResult = await dialogue_service.process_message(user_msg)

    chat_response = _build_chat_response(process_result)
    return chat_response


@chat_router.get('/api/chat/history')
async def history(sender_id: str) -> HistoryResponse:
    return HistoryResponse(
        sender_id=sender_id,
        messages=[
            HistoryMessage(role='user', text='你好'),
            HistoryMessage(role='bot', text='我不好'),
        ],
    )
