from pydantic import BaseModel, Field

from domain.message import UserMessage, BotMessage


class Turn(BaseModel):
    turn_id: str
    user_message: UserMessage
    bot_messages: list[BotMessage] = Field(default_factory=list)
