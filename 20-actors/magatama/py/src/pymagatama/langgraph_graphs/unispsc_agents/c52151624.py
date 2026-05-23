from typing import TypedDict
from langgraph.graph import StateGraph, END

class SharpenerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: SharpenerState):
    required = ['abrasive_material_type', 'safety_certification_standard']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

workflow = StateGraph(SharpenerState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
