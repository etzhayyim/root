from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScopeHandleState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_medical_spec(state: ScopeHandleState):
    required = ['regulatory_certification_number', 'voltage_compatibility']
    valid = all(k in state['spec_data'] for k in required)
    return {'is_compliant': valid}

graph = StateGraph(ScopeHandleState)
graph.add_node('validate', validate_medical_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
