from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IntraoralLightState(TypedDict):
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_specs(state: IntraoralLightState):
    errors = []
    if 'LuminousIntensity' not in state['specs']: errors.append('Missing intensity')
    if 'MedicalDeviceClass' != 'Class II': errors.append('Medical class mismatch')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(IntraoralLightState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()