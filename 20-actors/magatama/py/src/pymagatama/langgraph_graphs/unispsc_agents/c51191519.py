from typing import TypedDict
from langgraph.graph import StateGraph, END

class PamabromState(TypedDict):
    purity_level: float
    compliance_docs: list[str]
    approved: bool

def validate_purity(state: PamabromState):
    state['approved'] = state['purity_level'] >= 99.0
    return state

def check_docs(state: PamabromState):
    return {'approved': state['approved'] and len(state['compliance_docs']) >= 3}

graph = StateGraph(PamabromState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_docs', check_docs)
graph.add_edge('validate_purity', 'check_docs')
graph.add_edge('check_docs', END)
graph.set_entry_point('validate_purity')