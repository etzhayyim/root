from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlitterState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: GlitterState):
    required = ['size', 'material_safety', 'toxicity_check']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

workflow = StateGraph(GlitterState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
