from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class PolymerState(TypedDict):
    purity: float
    viscosity: float
    compliant: bool

def validate_polymer(state: PolymerState) -> PolymerState:
    if state['purity'] >= 99.5 and state['viscosity'] > 500:
        state['compliant'] = True
    else:
        state['compliant'] = False
    return state

def route_by_compliance(state: PolymerState) -> str:
    return 'process' if state['compliant'] else 'flag_error'

graph = StateGraph(PolymerState)
graph.add_node('validate', validate_polymer)
graph.add_node('process', lambda s: s)
graph.add_node('flag_error', lambda s: s)

graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph.add_edge('flag_error', END)
graph = graph.compile()