from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BleacherState(TypedDict):
    specs: dict
    is_compliant: bool
    safety_check_passed: bool

def validate_specs(state: BleacherState):
    required = ['structural_certification', 'occupant_load_capacity']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def safety_audit(state: BleacherState):
    state['safety_check_passed'] = state.get('is_compliant', False) and state['specs'].get('occupant_load_capacity', 0) > 0
    return state

graph = StateGraph(BleacherState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
