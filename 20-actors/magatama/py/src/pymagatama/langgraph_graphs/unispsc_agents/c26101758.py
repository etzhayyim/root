from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    hardness = state['specs'].get('hardness')
    state['approved'] = hardness >= 50
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()