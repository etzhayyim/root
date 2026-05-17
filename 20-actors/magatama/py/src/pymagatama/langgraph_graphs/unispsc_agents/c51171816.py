from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OndansetronState(TypedDict):
    batch_id: str
    quality_docs: List[str]
    status: str

def validate_gmp(state: OndansetronState):
    state['status'] = 'VALIDATED' if 'GMP_CERT' in state['quality_docs'] else 'FAILED'
    return state

def check_expiry(state: OndansetronState):
    return {'status': 'EXPIRED' if state.get('expired') else 'READY'}

graph = StateGraph(OndansetronState)
graph.add_node('validate', validate_gmp)
graph.add_node('expiry', check_expiry)
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph.set_entry_point('validate')
graph = graph.compile()