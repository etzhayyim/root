from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    purity: float
    activity_units: float
    spec_compliant: bool

def validate_purity(state: ReagentState):
    state['spec_compliant'] = state['purity'] >= 95.0
    return state

def check_stability(state: ReagentState):
    if state['activity_units'] < 1000:
        state['spec_compliant'] = False
    return state

graph = StateGraph(ReagentState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_stability', check_stability)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_stability')
graph.add_edge('check_stability', END)
graph = graph.compile()