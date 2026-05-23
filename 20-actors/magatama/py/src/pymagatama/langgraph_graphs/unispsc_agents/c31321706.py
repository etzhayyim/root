from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AssemblyState(TypedDict):
    material_specs: dict
    validation_passed: bool
    torque_requirements: float

def validate_material(state: AssemblyState):
    # Simulate material compliance check
    state['validation_passed'] = 'resistivity' in state['material_specs']
    return state

def check_torque(state: AssemblyState):
    # Simulate mechanical torque validation
    if state.get('torque_requirements', 0) > 0:
        return {'validation_passed': True}
    return {'validation_passed': False}

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_material)
graph.add_node('torque_check', check_torque)
graph.set_entry_point('validate')
graph.add_edge('validate', 'torque_check')
graph.add_edge('torque_check', END)
graph = graph.compile()
