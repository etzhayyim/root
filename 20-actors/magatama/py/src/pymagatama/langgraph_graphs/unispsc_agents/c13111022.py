from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    purity: float
    safety_verified: bool
    traceable: bool

def validate_purity(state: MineralState) -> MineralState:
    if state['purity'] >= 99.9:
        state['safety_verified'] = True
    return state

def verify_traceability(state: MineralState) -> MineralState:
    if state['batch_id'].startswith('RAW-'):
        state['traceable'] = True
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('trace', verify_traceability)
graph.set_entry_point('validate')
graph.add_edge('validate', 'trace')
graph.add_edge('trace', END)
graph = graph.compile()