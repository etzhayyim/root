from typing import TypedDict
from langgraph.graph import StateGraph, END

class EnemaState(TypedDict):
    capacity_ml: int
    material: str
    is_sterile: bool
    validation_passed: bool

def validate_specs(state: EnemaState):
    state['validation_passed'] = (state['capacity_ml'] > 0 and state['is_sterile'] == True)
    return state

graph = StateGraph(EnemaState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
