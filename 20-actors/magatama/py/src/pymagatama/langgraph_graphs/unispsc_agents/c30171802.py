from typing import TypedDict
from langgraph.graph import StateGraph, END

class SkylightState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: SkylightState):
    required = ['U-Value', 'Water_Tightness']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Failed'}

workflow = StateGraph(SkylightState)
workflow.add_node('validator', validate_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()
