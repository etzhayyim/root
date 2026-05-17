from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpectroState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_optics(state: SpectroState):
    resolution = state['spec_data'].get('resolution', 0)
    state['validation_passed'] = resolution > 0.01
    return state

workflow = StateGraph(SpectroState)
workflow.add_node('validate', validate_optics)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()