from typing import TypedDict
from langgraph.graph import StateGraph, END

class RollerState(TypedDict):
    specs: dict
    is_validated: bool

def validate_specs(state: RollerState):
    required = ['spike_length_mm', 'roller_width_mm']
    valid = all(k in state['specs'] for k in required)
    return {'is_validated': valid}

workflow = StateGraph(RollerState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
