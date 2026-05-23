from typing import TypedDict
from langgraph.graph import StateGraph, END

class QuickDisconnectState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_specs(state: QuickDisconnectState):
    pressure = state['spec_data'].get('pressure_rating', 0)
    state['validated'] = pressure > 0
    return state

def generate_compliance(state: QuickDisconnectState):
    state['compliance_report'] = 'Compliant' if state['validated'] else 'Non-compliant'
    return state

graph = StateGraph(QuickDisconnectState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
