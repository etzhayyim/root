from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolingState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_risk: str

def validate_specs(state: ToolingState) -> ToolingState:
    required = ['Material composition', 'Tolerance grade']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state

def check_compliance(state: ToolingState) -> ToolingState:
    state['compliance_risk'] = 'EXEMPT' if state['validated'] else 'EXPORT_CONTROL_REQUIRED'
    return state

graph = StateGraph(ToolingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
