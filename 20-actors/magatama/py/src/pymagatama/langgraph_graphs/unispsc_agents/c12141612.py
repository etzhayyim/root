from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AdhesiveState(TypedDict):
    viscosity: float
    curing_required: bool
    safety_check: List[str]
    approved: bool

def validate_viscosity(state: AdhesiveState) -> AdhesiveState:
    state['approved'] = state['viscosity'] > 500.0
    return state

def check_safety_protocols(state: AdhesiveState) -> AdhesiveState:
    state['safety_check'].append('MSDS_REVIEWED')
    state['safety_check'].append('DANGEROUS_GOODS_LABELED')
    return state

graph = StateGraph(AdhesiveState)
graph.add_node('validate', validate_viscosity)
graph.add_node('safety', check_safety_protocols)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
