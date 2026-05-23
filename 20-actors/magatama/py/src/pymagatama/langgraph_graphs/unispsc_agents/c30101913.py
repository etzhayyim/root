from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TinState(TypedDict):
    coil_id: str
    purity_level: float
    thickness: float
    is_compliant: bool

def validate_specs(state: TinState) -> TinState:
    state['is_compliant'] = state['purity_level'] >= 99.9 and state['thickness'] > 0
    return state

def route_processing(state: TinState) -> str:
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(TinState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_processing, {'process': 'process', 'reject': END})
graph.add_edge('process', END)
graph = graph.compile()
