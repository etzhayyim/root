from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalSupplyState(TypedDict):
    part_number: str
    is_sterile: bool
    compliance_docs: list
    status: str

def validate_sterility(state: MedicalSupplyState):
    state['status'] = 'Validating' if state['is_sterile'] else 'Rejected'
    return state

def check_compliance(state: MedicalSupplyState):
    if len(state['compliance_docs']) >= 3:
        state['status'] = 'Approved'
    else:
        state['status'] = 'Pending Compliance Review'
    return state

graph = StateGraph(MedicalSupplyState)
graph.add_node('validate', validate_sterility)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()