from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrakingSystemState(TypedDict):
    spec_data: dict
    validation_passed: bool
    safety_certification: List[str]

def validate_braking_specs(state: BrakingSystemState):
    required_keys = ['braking_force', 'sil_level']
    passed = all(key in state['spec_data'] for key in required_keys)
    return {'validation_passed': passed}

def check_compliance(state: BrakingSystemState):
    if state['validation_passed'] and 'ISO26262' in state['safety_certification']:
        return 'approved'
    return 'rejected'

graph = StateGraph(BrakingSystemState)
graph.add_node('validate', validate_braking_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)