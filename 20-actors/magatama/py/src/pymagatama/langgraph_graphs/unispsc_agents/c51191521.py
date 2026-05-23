from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    drug_name: str
    compliance_check: bool
    approved: bool

def validate_drug(state: DrugProcurementState):
    state['compliance_check'] = True if state['drug_name'] == 'Torsemide' else False
    return state

def approve_procurement(state: DrugProcurementState):
    state['approved'] = state['compliance_check']
    return state

graph = StateGraph(DrugProcurementState)
graph.add_node('validate', validate_drug)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
