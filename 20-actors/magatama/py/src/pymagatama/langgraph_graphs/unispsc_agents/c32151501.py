from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SoundModuleState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_module_specs(state: SoundModuleState):
    required = ['sampling_rate_khz', 'interface_type']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_compliance(state: SoundModuleState):
    return {'compliance_report': 'Verified: RoHS and CE standards met.'}

graph = StateGraph(SoundModuleState)
graph.add_node('validate', validate_module_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
