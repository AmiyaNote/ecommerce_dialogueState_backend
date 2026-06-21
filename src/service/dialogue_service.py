from domain.message import UserMessage, ProcessResult
from domain.state import DialogueState
from engine.dialogue_engine import DialogueEngine
from repository.dialogue_state_repository import DialogueStateRepository


class DialogueService:
    def __init__(self,
                 dialogue_state_repository: DialogueStateRepository,
                 dialogue_engine: DialogueEngine):
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine = dialogue_engine


    async def process_message(self, user_message: UserMessage) -> ProcessResult:
        """
        1.获取state
        2.执行，修改，业务，state被改变
        3.state保存
        """
        state: DialogueState = await self.dialogue_state_repository.load_state(user_message.sender_id)

        process_result: ProcessResult = await self.dialogue_engine.process_message(state=state,
                                                                                   user_message=user_message)
        await self.dialogue_state_repository.save_state(state)

        return process_result
