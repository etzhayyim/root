from typing import TypedDict
from langgraph.graph import StateGraph, END

class EnemaSpecs(TypedDict):
    material: str
    volume_ml: int
    is_sterile: bool
    validation_passed: bool

def validate_specs(state: EnemaSpecs):
    state['validation_passed'] = state['is_sterile'] and state['volume_ml'] > 0
    return state

graph = StateGraph(EnemaSpecs)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
