from typing import TypedDict
from langgraph.graph import StateGraph, END

class FuelSystemState(TypedDict):
    material_specs: dict
    compliance_docs: list
    validation_passed: bool

def validate_materials(state: FuelSystemState):
    # logic to check material specs for fuel tank durability
    state['validation_passed'] = all(['thickness' in state['material_specs'], 'alloy' in state['material_specs']])
    return state

def check_compliance(state: FuelSystemState):
    # logic to verify UN/DOT certifications
    state['validation_passed'] = len(state['compliance_docs']) > 0
    return state

graph = StateGraph(FuelSystemState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_materials', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_materials')
graph = graph.compile()