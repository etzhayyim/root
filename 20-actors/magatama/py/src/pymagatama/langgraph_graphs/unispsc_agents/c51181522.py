from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    compliance_docs: bool
    is_approved: bool

def validate_purity(state: PharmState):
    state['is_approved'] = state['purity'] >= 99.0
    return state

def check_docs(state: PharmState):
    return {"is_approved": state['is_approved'] and state['compliance_docs']}

graph = StateGraph(PharmState)
graph.add_node("validate", validate_purity)
graph.add_node("check", check_docs)
graph.add_edge("validate", "check")
graph.add_edge("check", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()