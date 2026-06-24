import asyncio
import json
from typing import Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from channel.knowledge.knowledge_intent import KnowledgeIntent
from channel.task.flows import Flow, FlowsList
from client.llm import llm
from domain.message import UserMessage, MessageType
from domain.state import DialogueState
from plan.turn_models import TurnPlan
from prompts.history_builder import HistoryBuilder
from prompts.load_prompt_from_jinjia2 import load_prompt_from_jinja2


class TurnPlanner:
    """
    意图分析器
    作用：根据任务自然语言 调用LLM 分析轨道类型
    """

    async def predict(self,
                      state: DialogueState,
                      flows: FlowsList,
                      knowledge_intents: dict[str, KnowledgeIntent],
                      ) -> TurnPlan:
        """

        :param state:
        :return: 返回值是什么?(分析:定义数据模型)
        """

        """
            turn_plan 模板需要 7 个变量:
                    available_flows_json: 当前可用的任务流程列表 JSON。
                    knowledge_intents_json: 当前可用的知识类意图列表 JSON。
                    active_task_json: 当前正在执行的任务 JSON，没有则为 null。
                    interrupted_tasks_json: 当前被暂停/打断的任务列表 JSON。
                    focused_object_json: 当前对话聚焦的业务对象 JSON，没有则为 null。
                    current_conversation: 当前轮可参考的对话上下文 JSON。
                    user_message: 当前用户消息文本。
        """
        # 1. 构建提示词
        user_message = HistoryBuilder._render_user_message(state.pending_turn.user_message)
        history = HistoryBuilder.build(state.current_session().turns)
        active_task = state.active_task
        focused_object = state.focused_object
        _flows: list[Flow] = flows.flows

        available_flows = {
            "flows": [flow.model_dump(exclude={"steps"}) for flow in _flows]
        }
        active_task_data = active_task.model_dump() if active_task is not None else None
        interrupted_tasks = [task.model_dump() for task in state.paused_tasks]
        focused_object_data = focused_object.model_dump() if focused_object is not None else None
        knowledge_intents_data = [
            {"id": intent.intent, "description": ""}
            for intent in knowledge_intents.values()
        ]

        inputs_prompt = {
            "current_conversation": history,
            "user_message": user_message,
            "available_flows_json": json.dumps(available_flows, ensure_ascii=False),
            "active_task_json": json.dumps(active_task_data, ensure_ascii=False),
            "interrupted_tasks_json": json.dumps(interrupted_tasks, ensure_ascii=False),
            "focused_object_json": json.dumps(focused_object_data, ensure_ascii=False),
            "knowledge_intents_json": json.dumps(knowledge_intents_data, ensure_ascii=False),
        }

        print(json.dumps(inputs_prompt, ensure_ascii=False, indent=2))


        # 2. 调用LLM模型

        prompt_template_text = load_prompt_from_jinja2("turn_plan")

        prompt_template = PromptTemplate.from_template(template=prompt_template_text, template_format="jinja2")

        chain = prompt_template | llm | JsonOutputParser()

        llm_response_dict: dict[str, Any] = await chain.ainvoke(inputs_prompt)

        return TurnPlan.from_dict(llm_response_dict)


if __name__ == '__main__':
    from domain.context import TaskContext
    from domain.message import BotMessage, FocusedObject
    from domain.turn import Turn

    def build_mock_state() -> DialogueState:
        state = DialogueState(sender_id="test_sender")
        state.start_session()

        history_turn = Turn(
            turn_id="turn_history_001",
            user_message=UserMessage(
                sender_id="test_sender",
                message_id="msg_history_001",
                type=MessageType.TEXT,
                text="你好",
            ),
            bot_messages=[BotMessage(text="你好，我是电商助手，有什么可以帮您？")],
        )
        state.current_session().turns.append(history_turn)

        state.start_task(
            TaskContext(
                flow_id="order_status_query",
                step_id="ask_order_number",
                slots={},
            )
        )
        state.set_focused_object(
            FocusedObject(
                type="order",
                id="order_10001",
                title="iPhone 15 Pro",
                attributes={"status": "已发货"},
            )
        )
        state.begin_turn(
            UserMessage(
                sender_id="test_sender",
                message_id="msg_current_001",
                type=MessageType.TEXT,
                text="订单 10001 现在到哪了？",
            )
        )
        return state

    def build_mock_flows() -> FlowsList:
        return FlowsList(
            flows=[
                Flow(
                    id="order_status_query",
                    name="订单状态查询",
                    description="帮用户查询订单当前的处理状态",
                ),
                Flow(
                    id="refund_apply",
                    name="退款申请",
                    description="帮用户提交退款申请",
                ),
            ]
        )

    def build_mock_knowledge_intents() -> dict[str, KnowledgeIntent]:
        return {
            "shipping_policy": KnowledgeIntent(intent="shipping_policy"),
            "product_info": KnowledgeIntent(intent="product_info"),
        }

    def test_parse_turn_plan():
        """用模拟 LLM 输出测试反序列化，不调用真实 LLM"""
        mock_responses = [
            {
                "name": "knowledge",
                "data": {
                    "task": None,
                    "knowledge": {"intents": ["shipping_policy"]},
                    "chitchat": None,
                },
            },
            {
                "name": "task",
                "data": {
                    "task": {
                        "commands": [
                            {"command": "start_flow", "flow": "order_status_query"},
                            {"command": "set_slots", "slots": {"order_number": "10001"}},
                        ]
                    },
                    "knowledge": None,
                    "chitchat": None,
                },
            },
            {
                "name": "chitchat",
                "data": {
                    "task": None,
                    "knowledge": None,
                    "chitchat": {},
                },
            },
        ]
        print("=== TurnPlan.from_dict ===")
        for case in mock_responses:
            turn_plan = TurnPlan.from_dict(case["data"])
            print(f"[{case['name']}] {turn_plan.model_dump()}")



    async def test_predict():
        """调用 TurnPlanner.predict（需配置 LLM API Key）"""
        state = build_mock_state()
        flows = build_mock_flows()
        knowledge_intents = build_mock_knowledge_intents()
        turn_plan = await TurnPlanner().predict(state, flows, knowledge_intents)


        print("=== predict ===")
        # {"task":{"commands":[{"command":"set_slots"},{"command":"resume_flow"}]},"knowledge":null,"chitchat":null}
        print(json.dumps(turn_plan.model_dump(), ensure_ascii=False, indent=2))


    test_parse_turn_plan()
    asyncio.run(test_predict())
