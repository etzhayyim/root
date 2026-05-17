from typing import TypedDict
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: FreezerState):
    temp = state['specs'].get('temp', 0)
    state['validation_passed'] = temp <= -150
    state['compliance_report'] = 'Validated' if state['validation_passed'] else 'Failed Temperature Criteria'
    return state

graph = StateGraph(FreezerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()