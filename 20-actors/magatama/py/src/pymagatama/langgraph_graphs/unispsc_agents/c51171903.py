from typing import TypedDict
from langgraph.graph import StateGraph, END

class NizatidineState(TypedDict):
    purity: float
    compliance_docs: bool
    is_approved: bool

def check_purity(state: NizatidineState):
    return {'is_approved': state['purity'] >= 99.0 and state['compliance_docs']}

def route_by_approval(state: NizatidineState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(NizatidineState)
graph.add_node('check', check_purity)
graph.add_edge('check', END)
graph.set_entry_point('check')
compiled_graph = graph.compile()
