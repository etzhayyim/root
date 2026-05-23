from langgraph.graph import StateGraph, END
from typing import TypedDict

class PerfusionState(TypedDict):
    filter_id: str
    specifications: dict
    approved: bool

def validate_specs(state: PerfusionState):
    pore_size = state['specifications'].get('pore_size_microns', 0)
    if 0.1 <= pore_size <= 5.0:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(PerfusionState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
