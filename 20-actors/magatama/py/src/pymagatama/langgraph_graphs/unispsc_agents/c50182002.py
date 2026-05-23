from typing import TypedDict
from langgraph.graph import StateGraph, END

class FrozenGoodsState(TypedDict):
    temp_log: list
    is_compliant: bool

def validate_cold_chain(state: FrozenGoodsState):
    state['is_compliant'] = all([-25 <= t <= -18 for t in state['temp_log']])
    return state

graph = StateGraph(FrozenGoodsState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
