from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_number: str
    compliance_docs: List[str]
    validated: bool

def validate_medical_compliance(state: ProcurementState):
    required = {'iso_13485', 'fda_clearance', 'sterilization_cert'}
    state['validated'] = required.issubset(set(state['compliance_docs']))
    return state

def route_by_validation(state: ProcurementState):
    return 'valid' if state['validated'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()