from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    temp_rating: int
    safety_verified: bool
    is_compliant: bool

def validate_specs(state: FurnaceState):
    state['is_compliant'] = state['temp_rating'] >= 1200 and state['safety_verified']
    return state

workflow = StateGraph(FurnaceState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
