from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingSpecState(TypedDict):
    curing_time: float
    tensile_strength: float
    compliance_check: bool

def validate_casting_specs(state: CastingSpecState):
    state['compliance_check'] = state['curing_time'] < 10.0 and state['tensile_strength'] > 500.0
    return state

graph = StateGraph(CastingSpecState)
graph.add_node('validate', validate_casting_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()