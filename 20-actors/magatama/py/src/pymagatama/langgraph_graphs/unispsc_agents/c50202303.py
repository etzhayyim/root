from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FrozenJuiceState(TypedDict):
    batch_id: str
    temp_log: float
    inspection_passed: bool

def validate_cold_chain(state: FrozenJuiceState):
    state['inspection_passed'] = state['temp_log'] <= -18.0
    return state

def route_by_quality(state: FrozenJuiceState):
    return 'accept' if state['inspection_passed'] else 'reject'

graph = StateGraph(FrozenJuiceState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_quality, {'accept': END, 'reject': END})

graph = graph.compile()
