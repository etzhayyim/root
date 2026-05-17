from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    requires_cold_chain: bool
    clearance_status: str

def validate_certification(state: ReagentState):
    state['clearance_status'] = 'VALIDATED' if state.get('clearance_status') else 'PENDING'
    return state

def check_cold_chain(state: ReagentState):
    state['requires_cold_chain'] = True
    return 'Cold chain logistics required'

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_certification)
graph.add_node('logistics', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()