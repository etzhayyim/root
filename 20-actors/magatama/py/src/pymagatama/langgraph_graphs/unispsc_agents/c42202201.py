from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadioSurgeryComponentState(TypedDict):
    part_id: str
    validation_passed: bool
    shielding_data: dict
    approved: bool

def validate_shielding(state: RadioSurgeryComponentState):
    # Simulate CAD/Material shielding verification logic
    state['validation_passed'] = state['shielding_data'].get('lead_equivalence') >= 5.0
    return state

def check_certification(state: RadioSurgeryComponentState):
    state['approved'] = state.get('validation_passed', False)
    return state

graph = StateGraph(RadioSurgeryComponentState)
graph.add_node('validate', validate_shielding)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()