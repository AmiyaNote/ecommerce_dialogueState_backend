from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class TaskContext(BaseModel):
    """
    Runtime snapshot for a user flow.
    """

    flow_id: str
    step_id: str
    slots: dict[str, Any] = Field(default_factory=dict)


class SystemContext(BaseModel):
    flow_id: str
    step_id: str 



class StartedSystemContext(SystemContext):
    flow_id: Literal["system_task_started"]
    started_flow_id: str 
    started_step_id: str 


class InterruptedSystemContext(SystemContext):
    flow_id: Literal["system_task_interrupted"]
    interrupted_flow_id: str 
    interrupted_flow_name: str
    started_flow_id: str
    started_flow_name: str


class CanceledSystemContext(SystemContext):
    flow_id: Literal["system_task_canceled"]
    canceled_flow_id: str
    canceled_flow_name: str


class ResumedSystemContext(SystemContext):
    flow_id: Literal["system_task_resumed"]
    resumed_flow_id: str
    resumed_flow_name: str


class CollectSystemContext(SystemContext):
    flow_id: Literal["system_collect_information"]
    slot_name: str
    response : dict[str, Any] = Field(default_factory=dict)


AnySystemContext = Annotated[
    StartedSystemContext
    | InterruptedSystemContext
    | CanceledSystemContext
    | ResumedSystemContext
    | CollectSystemContext,
    Field(discriminator="flow_id"),
]


FLOW_ID_TO_CONTEXT_CLASS: dict[str, type[SystemContext]] = {
    "system_task_started": StartedSystemContext,
    "system_task_interrupted": InterruptedSystemContext,
    "system_task_canceled": CanceledSystemContext,
    "system_task_resumed": ResumedSystemContext,
    "system_collect_information": CollectSystemContext
}
