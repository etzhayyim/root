from typing import TypedDict
from langgraph.graph import StateGraph, END

class InstrumentState(TypedDict):
    instrument_type: str
    quality_score: float
    inspection_passed: bool

def validate_instrument(state: InstrumentState):
    state['inspection_passed'] = state['quality_score'] > 0.9
    return state

graph = StateGraph(InstrumentState)
graph.add_node('inspection', validate_instrument)
graph.set_entry_point('inspection')
graph.add_edge('inspection', END)
compiled_graph = graph.compile()