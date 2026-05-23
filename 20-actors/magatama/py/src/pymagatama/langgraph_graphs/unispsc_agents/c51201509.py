from typing import TypedDict
from langgraph.graph import StateGraph, END

class BioPharmaState(TypedDict):
    batch_id: str
    temp_log: list
    gmp_status: bool
    approved: bool

def validate_cold_chain(state: BioPharmaState):
    state['approved'] = all(t < 8 for t in state['temp_log']) and state['gmp_status']
    return state

graph = StateGraph(BioPharmaState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
