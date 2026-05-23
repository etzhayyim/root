from typing import TypedDict
from langgraph.graph import StateGraph, END

class EnemaState(TypedDict):
    product_specs: dict
    compliance_verified: bool

def validate_medical_compliance(state: EnemaState):
    # Simulate validation of ISO certification
    is_compliant = state['product_specs'].get('ISO_13485', False)
    return {'compliance_verified': is_compliant}

def prepare_logistics(state: EnemaState):
    return {'compliance_verified': state['compliance_verified']}

graph = StateGraph(EnemaState)
graph.add_node('validate', validate_medical_compliance)
graph.add_node('logistics', prepare_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
app = graph.compile()
