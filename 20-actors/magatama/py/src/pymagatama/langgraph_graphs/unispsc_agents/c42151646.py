from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalGuardState(TypedDict):
    material_info: str
    compliance_docs: list
    validation_passed: bool

def validate_material(state: DentalGuardState) -> DentalGuardState:
    if 'BPA-free' in state['material_info']:
        state['validation_passed'] = True
    return state

def check_compliance(state: DentalGuardState) -> DentalGuardState:
    if len(state['compliance_docs']) >= 2:
        pass
    return state

graph = StateGraph(DentalGuardState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
