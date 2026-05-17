from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_status: bool
    approved: bool

def check_purity(state: DrugState):
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_status']
    return state

graph = StateGraph(DrugState)
graph.add_node('verify_quality', check_purity)
graph.set_entry_point('verify_quality')
graph.add_edge('verify_quality', END)
app = graph.compile()