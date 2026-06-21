import json
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.state import DialogueState
from model.DialogueStateRecord import DialogueStateRecord


class DialogueStateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def load_state(self, sender_id: str) -> DialogueState:
        sql = select(DialogueStateRecord).where(
            DialogueStateRecord.sender_id == sender_id
        )
        result = await self.session.execute(sql)
        state: DialogueStateRecord = result.scalar_one_or_none()
        if state:
            state_dict = json.loads(state.state_json)
            # state_dict 反序列化 为 DialogueState
            return DialogueState.model_validate(state_dict)

        else:
            # mysql没有，就新建一个兜底
            return DialogueState(sender_id=sender_id)

    async def save_state(self, state: DialogueState):
        # 将 state 序列化为一个 json 字符串
        state_json = json.dumps(state.model_dump(mode="json"), ensure_ascii=False)

        insert_stmt = insert(DialogueStateRecord).values(
            sender_id=state.sender_id, state_json=state_json
        )
        # `on_duplicate_key_update` 把它变成 **upsert**：如果这个 `sender_id` 已存在，就改成 `UPDATE state_json`
        upsert_stmt = insert_stmt.on_duplicate_key_update(
            state_json=insert_stmt.inserted.state_json
        )

        await self.session.execute(upsert_stmt)
        await self.session.commit()
