from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoomVangState(TypedDict):
    load_capacity: float
    material: str
    is_certified: bool
    validation_passed: bool

def validate_specs(state: BoomVangState):
    passed = state['load_capacity'] > 0 and state['is_certified'] is True
    return {'validation_passed': passed}

graph = StateGraph(BoomVangState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

app = graph.compile()
