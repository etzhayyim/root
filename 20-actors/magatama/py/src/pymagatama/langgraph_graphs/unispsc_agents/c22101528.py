from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticalState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_alignment_spec(state: OpticalState):
    accuracy = state['spec_data'].get('accuracy', 0)
    state['validated'] = accuracy < 0.5
    state['compliance_report'] = 'Pass' if state['validated'] else 'Fail: Alignment tolerance too high'
    return state

graph = StateGraph(OpticalState)
graph.add_node('validate', validate_alignment_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()