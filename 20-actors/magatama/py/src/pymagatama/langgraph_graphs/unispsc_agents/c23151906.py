from typing import TypedDict
from langgraph.graph import StateGraph, END

class LatheState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_risk: str

def validate_lathe_specs(state: LatheState):
    specs = state.get('spec_data', {})
    state['validated'] = 'power_rating' in specs and 'cnc' in specs
    return 'valid' if state['validated'] else 'invalid'

def check_dual_use(state: LatheState):
    state['compliance_risk'] = 'high' if state.get('spec_data', {}).get('precision', 0) < 0.005 else 'low'
    return state

graph = StateGraph(LatheState)
graph.add_node('validate', validate_lathe_specs)
graph.add_node('compliance', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()
