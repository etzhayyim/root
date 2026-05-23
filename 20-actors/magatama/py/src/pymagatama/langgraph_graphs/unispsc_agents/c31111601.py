from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validated: bool
    compliance_risk: str

def validate_alloy_specs(state: ExtrusionState):
    alloy = state['specs'].get('alloy', '')
    return {'validated': alloy in ['6061', '7075', '2024']}

def check_compliance(state: ExtrusionState):
    risk = 'HIGH' if state['specs'].get('precision_tolerances', False) else 'LOW'
    return {'compliance_risk': risk}

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_alloy_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
