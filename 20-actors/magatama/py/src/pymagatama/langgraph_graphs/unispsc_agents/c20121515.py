from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    servo_id: str
    spec_compliance: bool
    accuracy_test_results: float
    status: str

def validate_specs(state: ServoState) -> ServoState:
    # Logic to validate motor precision
    state['spec_compliance'] = state['accuracy_test_results'] < 0.01
    return state

def check_certification(state: ServoState) -> ServoState:
    state['status'] = 'CERTIFIED' if state['spec_compliance'] else 'REJECTED'
    return state

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()