from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    material_name: str
    purity_level: float
    hazard_compliance: bool
    approved: bool

def validate_safety_specs(state: ChemicalProcurementState):
    state['hazard_compliance'] = state['purity_level'] >= 0.98
    return state

def approval_check(state: ChemicalProcurementState):
    state['approved'] = state['hazard_compliance']
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_safety_specs)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
