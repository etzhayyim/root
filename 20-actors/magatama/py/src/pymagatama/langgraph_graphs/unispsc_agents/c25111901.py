from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MarineSystemState(TypedDict):
    spec_sheet_url: str
    compliance_docs: List[str]
    validated: bool
    approval_status: str

def validate_compliance(state: MarineSystemState):
    # Simulate regulatory validation for marine equipment
    print(f'Validating specs for {state['spec_sheet_url']}')
    return {'validated': True}

def approval_step(state: MarineSystemState):
    return {'approval_status': 'APPROVED' if state['validated'] else 'REJECTED'}

graph = StateGraph(MarineSystemState)
graph.add_node('validate', validate_compliance)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()