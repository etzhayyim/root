from typing import TypedDict
from langgraph.graph import StateGraph, END

class VibeState(TypedDict):
    material_specs: str
    load_capacity: float
    validation_status: bool

def validate_specs(state: VibeState):
    state['validation_status'] = state['load_capacity'] > 0
    return state

workflow = StateGraph(VibeState)
workflow.add_node('validator', validate_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()