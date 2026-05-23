from typing import TypedDict
from langgraph.graph import StateGraph, END

class JointState(TypedDict):
    spec_data: dict
    validation_error: str
    approved: bool

def validate_specs(state: JointState):
    required = ['torque', 'material']
    if not all(k in state['spec_data'] for k in required):
        return {'validation_error': 'Missing core specs', 'approved': False}
    return {'approved': True}

def structural_integrity_check(state: JointState):
    if state.get('spec_data', {}).get('torque', 0) < 0:
        return {'validation_error': 'Invalid torque', 'approved': False}
    return {'approved': True}

graph = StateGraph(JointState)
graph.add_node('validator', validate_specs)
graph.add_node('load_tester', structural_integrity_check)
graph.set_entry_point('validator')
graph.add_edge('validator', 'load_tester')
graph.add_edge('load_tester', END)
compile = graph.compile()
