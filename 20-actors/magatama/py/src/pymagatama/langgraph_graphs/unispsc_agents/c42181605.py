from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodPressureState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_cuff_specs(state: BloodPressureState):
    has_iso = state['spec_data'].get('iso_certification')
    state['validation_passed'] = bool(has_iso)
    return state

graph = StateGraph(BloodPressureState)
graph.add_node('validate', validate_cuff_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()