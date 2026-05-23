from typing import TypedDict
from langgraph.graph import StateGraph, END

class TableState(TypedDict):
    spec_data: dict
    is_compliant: bool
    approval_status: str

def validate_medical_specs(state: TableState):
    required = ['load_capacity', 'certification']
    is_valid = all(k in state['spec_data'] for k in required)
    return {'is_compliant': is_valid}

def assign_approval(state: TableState):
    status = 'APPROVED' if state['is_compliant'] else 'REJECTED'
    return {'approval_status': status}

graph = StateGraph(TableState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('approve', assign_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
