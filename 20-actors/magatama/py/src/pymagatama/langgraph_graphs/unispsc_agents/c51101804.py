from typing import TypedDict
from langgraph.graph import StateGraph, END

class CiclopiroxState(TypedDict):
    purity: float
    is_compliant: bool
    status: str

def validate_purity(state: CiclopiroxState):
    if state['purity'] >= 99.0:
        return {'is_compliant': True, 'status': 'Validated'}
    return {'is_compliant': False, 'status': 'Rejected'}

def update_status(state: CiclopiroxState):
    return {'status': 'Complete' if state['is_compliant'] else 'Flagged for Review'}

graph = StateGraph(CiclopiroxState)
graph.add_node('validate', validate_purity)
graph.add_node('finalize', update_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
