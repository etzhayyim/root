from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterState(TypedDict):
    spec: dict
    validated: bool
    compliance_report: str

def validate_specs(state: FilterState):
    # Simulate spectral check logic
    state['validated'] = state['spec'].get('transmittance', 0) > 0.90
    return state

def compliance_check(state: FilterState):
    state['compliance_report'] = 'Passed export control screening' if state['validated'] else 'Failed'
    return state

graph = StateGraph(FilterState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()