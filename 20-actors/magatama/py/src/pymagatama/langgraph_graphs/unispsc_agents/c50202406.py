from typing import TypedDict
from langgraph.graph import StateGraph, END

class LimeJuiceState(TypedDict):
    brix: float
    ph: float
    is_compliant: bool

def validate_quality(state: LimeJuiceState):
    state['is_compliant'] = 6.0 <= state['brix'] <= 12.0 and 2.0 <= state['ph'] <= 2.8
    return state

graph = StateGraph(LimeJuiceState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
