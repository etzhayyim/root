from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipetteState(TypedDict):
    volume: float
    is_sterile: bool
    validation_passed: bool

def validate_pipette(state: PipetteState):
    state['validation_passed'] = state['volume'] > 0 and state['is_sterile']
    return state

graph = StateGraph(PipetteState)
graph.add_node('validate', validate_pipette)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
