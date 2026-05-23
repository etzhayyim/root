from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity_level: float
    trace_elements: List[str]
    validation_passed: bool

def check_purity(state: CatalystState):
    passed = state['purity_level'] >= 99.9
    return {'validation_passed': passed}

def approve_procurement(state: CatalystState):
    return {'validation_passed': True}

graph = StateGraph(CatalystState)
graph.add_node('check_purity', check_purity)
graph.add_node('approve', approve_procurement)
graph.add_edge('check_purity', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('check_purity')
graph = graph.compile()
