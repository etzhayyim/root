from typing import TypedDict
from langgraph.graph import StateGraph, END

class CladdingState(TypedDict):
    specs: dict
    is_verified: bool
    compliance_alert: bool

def validate_specs(state: CladdingState):
    required = ['DepositionRate', 'PowerSupplyRequirements']
    return {'is_verified': all(k in state['specs'] for k in required)}

def evaluate_compliance(state: CladdingState):
    alert = state['specs'].get('MaterialType') == 'Radioactive'
    return {'compliance_alert': alert}

graph = StateGraph(CladdingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', evaluate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
