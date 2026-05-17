from typing import TypedDict
from langgraph.graph import StateGraph, END

class BortState(TypedDict):
    grain_size: float
    purity: float
    export_cleared: bool

def validate_specs(state: BortState):
    if state['purity'] < 99.0:
        raise ValueError('Purity below industrial threshold')
    return {'export_cleared': True}

graph = StateGraph(BortState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()