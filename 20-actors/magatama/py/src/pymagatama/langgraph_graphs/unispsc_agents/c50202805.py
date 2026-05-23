from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    concentration: float
    purity_check: bool
    approved: bool

def validate_brix(state: ProcessingState):
    state['purity_check'] = state['concentration'] >= 60.0
    return state

def final_approval(state: ProcessingState):
    state['approved'] = state['purity_check']
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_brix)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
