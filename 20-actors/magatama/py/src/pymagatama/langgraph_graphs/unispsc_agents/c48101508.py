from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToasterProcurementState(TypedDict):
    voltage: str
    capacity: int
    certifications: list[str]
    status: str

def validate_specs(state: ToasterProcurementState):
    if state['voltage'] not in ['200V-3P', '100V-1P']: return {'status': 'REJECTED'}
    return {'status': 'VALIDATED'}

def check_compliance(state: ToasterProcurementState):
    if 'NSF' not in state['certifications']: return {'status': 'NON_COMPLIANT'}
    return {'status': 'APPROVED'}

graph = StateGraph(ToasterProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
