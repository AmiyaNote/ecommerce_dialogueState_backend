from channel.task.action.runner import ActionRunner
from channel.task.command.command import Command
from channel.task.command.command_processor import CommandProcessor
from channel.task.flow.executor import FlowExecutor
from channel.task.flow.flows import FlowsList
from domain.message import BotMessage
from domain.state import DialogueState


class TaskHandler:
    def __init__(self,
                 command_processor: CommandProcessor,
                 flows: FlowsList,
                 flow_executor: FlowExecutor,
                 action_runner: ActionRunner):
        self.command_processor = command_processor
        self.flows = flows
        self.flow_executor = flow_executor
        self.action_runner = action_runner

    async def handle(self, commands: list[Command], state: DialogueState) -> list[BotMessage]:
        # 阶段①:把命令应用到 state
        self.command_processor.run(commands, state, self.flows)
        # 阶段②:推进流程,生成回复(下一节)
        messages: list[BotMessage] = await self.flow_executor.run_task(
            state, self.flows, self.action_runner
        )
        return messages