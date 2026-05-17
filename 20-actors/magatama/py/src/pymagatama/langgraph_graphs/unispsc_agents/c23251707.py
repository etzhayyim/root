from typing import TypedDict
from langgraph.graph import StateGraph, END

class PressState(TypedDict):
    capacity_tons: int
    safety_certs: list
    validation_status: bool

def validate_specs(state: PressState):
    state['validation_status'] = state['capacity_tons'] > 0 and 'ISO16092' in state['safety_certs']
    return state

def check_compliance(state: PressState):
    print(f'Compliance check for press capacity: {state['capacity_tons']} tons')
    return 'valid' if state['validation_status'] else 'review'

workflow = StateGraph(PressState)
workflow.add_node('validator', validate_specs)
workflow.add_edge('validator', END)
workflow.set_entry_point('validator')
graph = workflow.compile()