from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: EquipmentState):
    # Simulate CAD/Spec validation for fitness hardware
    required = ['max_weight', 'safety_cert']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def compliance_check(state: EquipmentState):
    # Business logic for aerobic equipment standards
    if state.get('approved', False):
        print('Equipment meets ASTM/ISO standards.')
    return state

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()