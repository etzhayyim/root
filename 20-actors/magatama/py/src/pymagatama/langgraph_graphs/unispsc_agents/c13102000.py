from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity: float
    origin: str
    validation_passed: bool

def validate_purity(state: MineralState) -> MineralState:
    state['validation_passed'] = state['purity'] >= 99.5
    return state

def verify_origin(state: MineralState) -> MineralState:
    state['validation_passed'] = state['validation_passed'] and (state['origin'] != 'restricted_zone')
    return state

def build_mineral_graph():
    graph = StateGraph(MineralState)
    graph.add_node('validate_purity', validate_purity)
    graph.add_node('verify_origin', verify_origin)
    graph.set_entry_point('validate_purity')
    graph.add_edge('validate_purity', 'verify_origin')
    graph.add_edge('verify_origin', END)
    return graph.compile()

graph = build_mineral_graph()