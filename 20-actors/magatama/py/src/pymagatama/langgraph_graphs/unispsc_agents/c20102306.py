from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class RobotServoState(TypedDict):
    part_number: str
    torque_requirements: float
    ip_rating: str
    validation_passed: bool
    log: List[str]

def validate_specs(state: RobotServoState) -> RobotServoState:
    passed = state['torque_requirements'] > 0 and state['ip_rating'] in ['IP65', 'IP67']
    state['validation_passed'] = passed
    state['log'].append(f'Validation result: {passed}')
    return state

def check_certification(state: RobotServoState) -> RobotServoState:
    if state['validation_passed']:
        state['log'].append('Checking compliance with IEC 60034 standards')
    return state

def route_after_validation(state: RobotServoState) -> str:
    return 'check' if state['validation_passed'] else END

graph = StateGraph(RobotServoState)
graph.add_node('validate', validate_specs)
graph.add_node('check', check_certification)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_after_validation)
graph.add_edge('check', END)
graph = graph.compile()
