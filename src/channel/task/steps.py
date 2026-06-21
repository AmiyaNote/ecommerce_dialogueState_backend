from enum import Enum
from typing import List

from pydantic import BaseModel

from channel.task.links import FlowStepLink, StaticLink, ConditionalLink, FallbackLink


#
class ResponseDefinition(BaseModel):
    """
    只有user_flows.yml特有，用于返回会前端botMessage，索要 订单号，商品，退款原因 等等
    响应模式：
    static: 静态模式
    rephrase: 改写模式（LLM）
    """
    text: str  # AI的回复，必填
    model: str = "static"  # 响应的方式，可选，默认为静态
    prompt: str | None = None


class FlowStepType(Enum):
    """
    流程的步骤类型
    """
    START = "start"
    END = "end"
    ACTION = "action"
    COLLECT = "collect"


class FlowStep(BaseModel):
    """
    流程的步骤 ，核心模型，取名展示嵌套关系：FlowStep =  flow 下面的 step
    """
    id: str  # 步骤id，必填
    type: FlowStepType  # 步骤类型，必填
    next: List[FlowStepLink] = []  # 下一步的步骤id，必填
    description: str = ""  # 步骤描述

    # 什么情况下自定义 序列，反序列化？  当需要返回自定义子类的时候，用dict 对照取值
    @classmethod
    def from_dict(cls, data: dict) -> "FlowStep":
        step_type = data["type"]
        clz: (StartFlowStep | EndFlowStep | CollectFlowStep | ActionFlowStep) = STEP_TYPE_TO_CLASS[step_type]
        return clz.from_dict(data)

    @staticmethod
    def base_fields(data: dict) -> dict:
        return {
            "id": data["id"],
            "type": data["type"],
            "description": data.get("description", ""),
            "next": FlowStep.build_links(data["next"])
        }

    @staticmethod
    def build_links(link_data: str | List) -> List[FlowStepLink]:

        # 1. next是字符串
        if isinstance(link_data, str):
            return [StaticLink(target=link_data)]

        # 2. next是列表
        else:
            links = []
            for link_dict in link_data:
                if "if" in link_dict:
                    links.append(ConditionalLink(target=link_dict["then"], condition=link_dict["if"]))
                else:
                    links.append(FallbackLink(target=link_dict["else"]))
            return links


# ========4个type 衍生的子类step
class StartFlowStep(FlowStep):
    """
    流程步骤：开始
    """
    type: FlowStepType = FlowStepType.START

    @classmethod
    def from_dict(cls, data: dict) -> "StartFlowStep":
        return cls(**FlowStep.base_fields(data))


class EndFlowStep(FlowStep):
    """
    流程步骤：结束
    """
    type: FlowStepType = FlowStepType.END

    @classmethod
    def from_dict(cls, data: dict) -> "EndFlowStep":
        return cls(**FlowStep.base_fields(data))


class ActionFlowStep(FlowStep):
    """
    流程步骤：执行某一个动作
    """
    type: FlowStepType = FlowStepType.ACTION

    action: str  # 动作名称，必填
    args: dict | str = {}  # 动作参数，选填

    @classmethod
    def from_dict(cls, data: dict) -> "ActionFlowStep":
        return cls(
            **FlowStep.base_fields(data),
            action=data["action"],
            args=data.get("args", {})
        )


class CollectFlowStep(FlowStep):
    """
    流程步骤：收集某个槽位信息
    """
    type: FlowStepType = FlowStepType.COLLECT

    slot_name: str  # 槽位名称，必填
    response: ResponseDefinition  # 槽位相关的数据，必填

    @classmethod
    def from_dict(cls, data: dict) -> "CollectFlowStep":
        return cls(
            **FlowStep.base_fields(data),
            slot_name=data["slot_name"],
            response=ResponseDefinition(**data["response"])
        )


# 多态分发
STEP_TYPE_TO_CLASS = {
    "start": StartFlowStep,
    "action": ActionFlowStep,
    "collect": CollectFlowStep,
    "end": EndFlowStep
}

if __name__ == '__main__':
    # - if: "context.get('reason') == 'clarification_rejected'"
    #   then: clarification_rejected
    # - else: ask_rephrase

    # dict_data = {
    #     "id": "start",
    #     "type": "start",
    #     "next": [{
    #         "if": "context.get('reason') == 'clarification_rejected'",
    #         "then": "clarification_rejected"
    #     },{
    #         "else": "ask_rephrase"
    #     }]
    # }
    dict_data = {
        "id": "start",
        "type": "collect",
        "slot_name": "order_number",
        "response": {
            "model": "static",
            "text": "一句话"
        },
        "next": []
    }

    obj = FlowStep.from_dict(dict_data)

    print(obj)
