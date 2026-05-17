from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    purity: float
    temp_compliance: bool
    approved: bool

def validate_purity(state: DrugState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_cold_chain(state: DrugState):
    return {'temp_compliance': True}

graph = StateGraph(DrugState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', check_cold_chain)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()