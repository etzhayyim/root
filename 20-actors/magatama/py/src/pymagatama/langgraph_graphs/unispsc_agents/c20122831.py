from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotControlState(TypedDict):
    task_id: str
    parameters: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: RobotControlState):
    params = state['parameters']
    log = []
    if params.get('payload_capacity_kg', 0) > 50:
        log.append('Requires high-payload safety protocol.')
    return {'validation_log': log}

def compile_robot_logic(state: RobotControlState):
    return {'is_approved': True, 'validation_log': ['Logic compiled successfully.']}

graph = StateGraph(RobotControlState)
graph.add_node('validate', validate_specs)
graph.add_node('compile', compile_robot_logic)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compile')
graph.add_edge('compile', END)
graph = graph.compile()
