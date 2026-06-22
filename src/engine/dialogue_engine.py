import time

from domain.message import UserMessage, ProcessResult, BotMessage, MessageType
from domain.state import DialogueState

"""
用户消息
-> 加载 DialogueState
-> DialogueEngine 调度
-> Planner 判断三轨
-> Validator 校验
-> Task / Knowledge / Chitchat 分发
-> Task 轨用 CommandProcessor + FlowExecutor + Action 推进
-> 保存 DialogueState
"""

class DialogueEngine:
    """
    DialogueEngine：是一轮对话的总入口，和总调度器
    LLM：底层能力，负责理解文本
    TurnPlanner：包装 LLM 的“本轮路由决策器”
    """

    # async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
    #     return ProcessResult(
    #         sender_id=user_message.sender_id,
    #         message_id=user_message.message_id,
    #         messages=[BotMessage(text="（暂时站位）你好！我收到了你的回复。")]
    #
    #     )

    async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        """
        # 1. 准备会话
        # 2. 开启本轮turn
        # 3. 按消息类型分流
        # 4. 把本轮回复写入turn
        # 5. 组装返回结果
        """
        """处理一条消息，直接修改 state，返回本轮结果。"""
        # 1. 准备会话(超时检查/新建)
        self._prepare_session(state)
        # 2. 开启本轮 turn(写入 pending_turn)
        self._begin_turn(state, user_message)

        # 3. 按消息类型分流
        if user_message.type is MessageType.TEXT:
            messages = await self._handle_text_message(state=state)
        else:
            # 对象消息(本节不实现,后面讲)
            messages = [BotMessage(text="暂不支持对象消息")]

        # 4. 把本轮回复的bot_messages写入pending_turn， pending_turn写入session的turns
        # extend(messages)：把本轮 bot 回复写入 pending_turn.bot_messages
        # commit_pending_turn()：把这个 pending_turn 追加到当前 session 的 turns 历史里，然后清空 pending_turn
        state.pending_turn.bot_messages.extend(messages)
        state.commit_pending_turn()

        # 5. 组装返回结果
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=messages,
        )

    def _prepare_session(self, state: DialogueState) -> None:
        session = state.current_session()
        now = time.time()
        if session is None:
            state.start_session()
            return
        if now - session.last_activity_at > 60 * 60:
            state.close_current_session()
            state.reset_runtime_state_for_new_session()
            state.start_session()
        else:
            session.last_activity_at = now

    @staticmethod
    def _begin_turn(state: DialogueState, message: UserMessage) -> None:
        state.begin_turn(message)

    async def _handle_text_message(self, state: DialogueState) -> list[BotMessage]:
        # TODO: mock data placeholder. Replace with real TurnPlanner/Validator/Handler flow later.
        return [BotMessage(text="（模拟数据）已收到你的消息，后续会接入真实意图识别和流程分发。")]
