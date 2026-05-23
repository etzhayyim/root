from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodPressureState(TypedDict):
    cuff_spec: dict
    validation_passed: bool

def validate_cuff_specs(state: BloodPressureState):
    # Business logic for verifying medical grade cuff specs
    required = ['size', 'material', 'connector']
    state['validation_passed'] = all(k in state['cuff_spec'] for k in required)
    return state

workflow = StateGraph(BloodPressureState)
workflow.add_node('validation', validate_cuff_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
