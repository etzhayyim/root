from typing import TypedDict
from langgraph.graph import StateGraph, END

class MannitolState(TypedDict):
    purity_level: float
    compliance_docs: list
    is_approved: bool

def validate_purity(state: MannitolState):
    state['is_approved'] = state['purity_level'] >= 98.0
    return state

def check_documentation(state: MannitolState):
    required = {'COA', 'SDS'}
    state['is_approved'] &= all(doc in state['compliance_docs'] for doc in required)
    return state

graph = StateGraph(MannitolState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_documentation', check_documentation)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_documentation')
graph.add_edge('check_documentation', END)
graph = graph.compile()
