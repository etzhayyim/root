from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlooringState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_materials(state: FlooringState):
    check = state['spec_data'].get('moisture_content', 0) < 12
    return {'validation_passed': check}

graph = StateGraph(FlooringState)
graph.add_node('validation', validate_materials)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
