"""
    loader 负责把 user_flows.yml 这类 YAML 配置文件加载并解析成 FlowsList。
    FlowsList 是内存中的流程集合，里面包含 user_flows.yml 里定义的所有 Flow。
"""
from pathlib import Path
from typing import List

import yaml

from channel.task.flow.flows import Flow, FlowsList, FlowSlot

from channel.task.flow.steps import FlowStep

base_path = Path(__file__).parents[2]
user_flow_path = base_path / "flow_config" / "user_flows.yml"
system_flow_path = base_path / "flow_config" / "system_flows.yml"


def load_yml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a dict: {path}")

    return data


def load_flows_from_file(path: Path) -> FlowsList:
    data = load_yml(path)

    slot_items = dict(data.get("slots", {}))

    slots = {
        slot_name: FlowSlot(name=slot_name, **slot_data) for slot_name, slot_data in slot_items.items()
    }

    flow_items = dict(data.get("flows", {}))

    # easy 写法：直接给出模拟结果，vibe自动与输入匹配，拼装。
    flows = []
    for flow_id, flow_data in flow_items.items():
        step_data_list = flow_data.get("steps", [])
        flows.append(
            Flow(
                id=flow_id,
                name=flow_data.get("name"),
                description=flow_data.get("description", ""),
                steps=[FlowStep.from_dict(step_data) for step_data in step_data_list],
            )
        )

    return FlowsList(flows=flows, slots=slots)


def load_flows_from_files(paths: List[Path]) -> FlowsList:
    flows = []
    slots = {}
    flow_ids = set()

    for path in paths:
        flow_list = load_flows_from_file(path)

        for flow in flow_list.flows:
            if flow.id in flow_ids:
                raise ValueError(f"Duplicate flow id '{flow.id}' in {path}")
            flow_ids.add(flow.id)
            flows.append(flow)

        for slot_name, slot in flow_list.slots.items():
            if slot_name in slots:
                raise ValueError(f"Duplicate slot name '{slot_name}' in {path}")
            slots[slot_name] = slot

    return FlowsList(flows=flows, slots=slots)

flow_list : FlowsList = load_flows_from_files(paths=[user_flow_path, system_flow_path])

if __name__ == "__main__":
    user_flows = load_flows_from_file(user_flow_path)
    system_flows = load_flows_from_file(system_flow_path)
    all_flows = load_flows_from_files([user_flow_path, system_flow_path])

    print(flow_list.model_dump_json(indent=2))
