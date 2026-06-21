from domain.message import UserMessage, ProcessResult, BotMessage
from domain.state import DialogueState


class DialogueEngine:
    """
    先站位
    """

    async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=[BotMessage(text="（暂时站位）你好！我收到了你的回复。")]

        )
