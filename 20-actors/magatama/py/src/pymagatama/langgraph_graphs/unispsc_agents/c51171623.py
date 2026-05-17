from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    purity: float
    safety_path: str
    is_approved: bool

def validate_purity(state: ReagentState):
    state['is_approved'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ReagentState):
    state['safety_path'] = 'verified' if state['is_approved'] else 'flagged'
    return state

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()