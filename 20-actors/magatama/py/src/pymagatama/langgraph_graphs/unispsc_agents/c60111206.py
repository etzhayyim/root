from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DecorState(TypedDict):
    material: str
    glitter_retention: float
    compliant: bool

def validate_safety(state: DecorState) -> DecorState:
    state['compliant'] = state['material'] == 'non-toxic' and state['glitter_retention'] > 0.9
    return state

def route_by_compliance(state: DecorState) -> str:
    return 'process' if state['compliant'] else END

def finalize_procurement(state: DecorState) -> DecorState:
    print('Procurement finalized for decoration materials')
    return state

graph = StateGraph(DecorState)
graph.add_node('validate', validate_safety)
graph.add_node('process', finalize_procurement)
graph.add_edge('validate', 'process')
graph.set_entry_point('validate')
graph.set_finish_point('process')
graph = graph.compile()
