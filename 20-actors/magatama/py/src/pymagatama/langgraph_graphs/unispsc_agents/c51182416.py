from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity_level: float
    has_coa: bool
    approved: bool

def validate_compliance(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0 and state['has_coa'] is True
    return state

def check_storage_requirements(state: ProcurementState):
    print(f'Verifying cold chain for {state['material_name']}')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('storage', check_storage_requirements)
graph.set_entry_point('validate')
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph = graph.compile()
