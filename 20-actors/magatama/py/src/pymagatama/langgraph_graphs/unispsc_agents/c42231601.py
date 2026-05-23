from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    tube_spec: dict
    validation_passed: bool
    compliance_status: str

def validate_medical_spec(state: ProcurementState):
    # Business logic for PEG tube procurement validation
    is_compliant = 'ISO 13485' in state['tube_spec'].get('standards', [])
    return {'validation_passed': is_compliant, 'compliance_status': 'verified' if is_compliant else 'failed'}

def route_procurement(state: ProcurementState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_spec)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement)
graph.add_edge('process', END)

app = graph.compile()
