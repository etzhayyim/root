from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingRobotState(TypedDict):
    robot_id: str
    specs: dict
    validation_status: str

def validate_robot_specs(state: WeldingRobotState):
    print(f'Validating specs for {state["robot_id"]}')
    return {'validation_status': 'PASSED'}

def route_by_validation(state: WeldingRobotState):
    return 'process_order' if state['validation_status'] == 'PASSED' else 'flag_error'

graph = StateGraph(WeldingRobotState)
graph.add_node('validate', validate_robot_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()