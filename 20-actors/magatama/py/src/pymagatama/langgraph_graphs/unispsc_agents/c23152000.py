from typing import TypedDict
from langgraph.graph import StateGraph, END

class EngineProcessState(TypedDict):
    spec_data: dict
    validation_passed: bool
    engine_status: str

def validate_specs(state: EngineProcessState):
    specs = state['spec_data']
    passed = 'power_output_kw' in specs and 'emission_compliance_standard' in specs
    return {'validation_passed': passed, 'engine_status': 'Validated' if passed else 'Error'}

workflow = StateGraph(EngineProcessState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
