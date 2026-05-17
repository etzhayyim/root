from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GasState(TypedDict):
    commodity_code: str
    volume: float
    purity: float
    validated: bool
    pipeline_ready: bool

def validate_quality(state: GasState):
    state['validated'] = state['purity'] >= 0.98
    return state

def check_pipeline(state: GasState):
    state['pipeline_ready'] = state['validated']
    return state

graph = StateGraph(GasState)
graph.add_node('validate', validate_quality)
graph.add_node('pipeline', check_pipeline)
graph.set_entry_point('validate')
graph.add_edge('validate', 'pipeline')
graph.add_edge('pipeline', END)

compiled_graph = graph.compile()