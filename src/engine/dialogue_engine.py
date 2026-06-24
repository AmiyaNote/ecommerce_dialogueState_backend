import time

from channel.knowledge.knowledge_handler import KnowledgeHandler
from channel.task.task_handler import TaskHandler
import conf.load_yml
from channel.task.flows import FlowsList
from domain.message import UserMessage, ProcessResult, BotMessage, MessageType
from domain.state import DialogueState
from plan.turn_models import TurnPlan
from plan.turn_planner import TurnPlanner

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


    第一次占位：
        async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=[BotMessage(text="（暂时站位）你好！我收到了你的回复。")]

        )

    """
    # 完整init后，再更新builder

    def __init__(self,
                 turn_planner: TurnPlanner,
                 # turn_validator: TurnPlanValidator,
                 # clarify_responder: ClarifyResponder,
                 task_handler: TaskHandler,
                 knowledge_handler: KnowledgeHandler,
                 # chit_chat_handler: ChitChatHandler
                 ):
        self.turn_planner = turn_planner
        # self.turn_validator = turn_validator  # TurnPlan校验器（负责校验）
        # self.clarify_responder = clarify_responder  # 意图澄清器（响应澄清的内容）
        self.task_handler = task_handler  # 处理轨道是业务任务的
        self.knowledge_handler = knowledge_handler  # 处理轨道信息咨询的
        # self.chit_chat_handler = chit_chat_handler  # 处理轨道是闲聊的

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
        # 2. 开启本轮 plan(写入 pending_turn)
        state.begin_turn(user_message)

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

    async def _handle_text_message(self, state: DialogueState) -> list[BotMessage]:
        """
        # return [BotMessage(text="（模拟数据）已收到你的消息，后续会接入真实意图识别和流程分发。")]
        一开始黑盒边界没有梳理清楚,_handle_text_message大黑盒 -》实现turn_plan -》 剩余valid，taskhandler黑盒。
          保持闭环，按顺序逐个击破黑盒
        继续缩小黑盒返回：state信息 -> Planner分析意图返回turn_plan  -> 根据turn_plan返回识别BotMessage结果（把task执行 黑盒 ）
        temple参数暂时只给flows相关
        """
        # 1. 利用意图分析器调用LLM，确定任务轨道
        turn_plan: TurnPlan = await self.turn_planner.predict(state, self.task_handler.flows, self.knowledge_handler.intents)

        # 2. 先跳过
        # TODO: 实现turn_plan的校验合法性，然后澄清。

        # 3. 根据turn_plan,进行不同handler任务执行
