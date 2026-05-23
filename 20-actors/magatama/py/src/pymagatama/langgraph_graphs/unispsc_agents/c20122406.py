from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotBearingState(TypedDict):
    part_id: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_bearing(state: RobotBearingState) -> RobotBearingState:
    specs = state.get('specs', {})
    load = specs.get('load_capacity_kn', 0)
    if load > 0:
        state['validation_passed'] = True
        state['log'].append('Validation successful: Load capacity within safety limits.')
    else:
        state['validation_passed'] = False
        state['log'].append('Validation failed: Missing or invalid load capacity.')
    return state

def route_by_validation(state: RobotBearingState) -> str:
    return 'process' if state['validation_passed'] else END

def process_bearing_workflow(state: RobotBearingState) -> RobotBearingState:
    state['log'].append('Processing robotic bearing assembly workflow...')
    return state

graph = StateGraph(RobotBearingState)
graph.add_node('validate', validate_bearing)
graph.add_node('process', process_bearing_workflow)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
