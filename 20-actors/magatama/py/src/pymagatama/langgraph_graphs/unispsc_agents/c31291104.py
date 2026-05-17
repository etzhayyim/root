from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    material_grade: str
    pressure_rating: float
    inspection_passed: bool

def validate_specs(state: ExtrusionState):
    # Business logic for bronze component validation
    if state['pressure_rating'] > 5000:
        state['inspection_passed'] = True
    else:
        state['inspection_passed'] = False
    return state

workflow = StateGraph(ExtrusionState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()