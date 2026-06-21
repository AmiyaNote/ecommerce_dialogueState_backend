from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from client import mysql_client
from engine.dialogue_engine import DialogueEngine
from repository.dialogue_state_repository import DialogueStateRepository
from service.dialogue_service import DialogueService



# 每个请求只创建 session
async def get_session():
    async with mysql_client.session_factory()  as session:
        yield session

async def get_dialogue_state_repository(session: AsyncSession = Depends(get_session)):
    return DialogueStateRepository(session=session)

async def get_dialogue_engine() -> DialogueEngine:
    return DialogueEngine()

async def get_dialogue_service(
        dialogue_state_repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
        dialogue_engine: DialogueEngine = Depends(get_dialogue_engine)
) -> DialogueService:
    return DialogueService(dialogue_state_repository=dialogue_state_repository, dialogue_engine=dialogue_engine)
