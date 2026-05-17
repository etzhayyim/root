from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlasmaState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: PlasmaState):
    required = ['ArcVoltageRating', 'DutyCyclePercentage']
    state['validation_passed'] = all(k in state['spec_data'] for k in required)
    return state

workflow = StateGraph(PlasmaState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()