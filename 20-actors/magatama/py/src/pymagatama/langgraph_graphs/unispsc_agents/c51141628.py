from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    drug_name: str
    batch_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_gmp(state: PharmState) -> PharmState:
    if 'GMP_CERT' in state['compliance_docs']:
        state['is_approved'] = True
    return state

def route_verification(state: PharmState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(PharmState)
graph.add_node('verify_gmp', validate_gmp)
graph.set_entry_point('verify_gmp')
graph.add_edge('verify_gmp', END)
app = graph.compile()
