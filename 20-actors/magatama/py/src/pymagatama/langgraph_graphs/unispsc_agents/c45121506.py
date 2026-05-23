from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CameraState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_tags: List[str]

def validate_specs(state: CameraState):
    required = ['resolution', 'fov']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: CameraState):
    tags = ['standard-telecom']
    if state['specs'].get('encryption'): tags.append('secure-verified')
    return {'compliance_tags': tags}

graph = StateGraph(CameraState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
