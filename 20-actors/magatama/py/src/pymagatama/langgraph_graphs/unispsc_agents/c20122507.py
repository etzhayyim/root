from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    servo_id: str
    spec_requirements: dict
    validation_log: List[str]
    is_approved: bool

def validate_torque(state: ServoState) -> ServoState:
    state['validation_log'].append('Verifying torque capacity against industry standards.')
    return state

def check_compliance(state: ServoState) -> ServoState:
    state['validation_log'].append('Checking dual-use compliance for export.')
    state['is_approved'] = True
    return state

graph = StateGraph(ServoState)
graph.add_node('validate', validate_torque)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()