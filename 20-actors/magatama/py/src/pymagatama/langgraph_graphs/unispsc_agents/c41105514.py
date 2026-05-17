from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    purity_check: bool
    storage_temp: str
    is_sterile: bool

def validate_purity(state: ReagentState):
    state['purity_check'] = True
    return 'Purity verified'

def check_cold_chain(state: ReagentState):
    return 'Cold chain protocols active'

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', check_cold_chain)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()