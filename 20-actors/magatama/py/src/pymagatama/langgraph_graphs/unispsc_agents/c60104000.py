from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BioMaterialState(TypedDict):
    material_id: str
    purity_level: float
    safety_clearance: bool
    validation_steps: List[str]

def validate_compliance(state: BioMaterialState):
    state['validation_steps'].append('Compliance Check Initiated')
    state['safety_clearance'] = state['purity_level'] >= 99.0
    return state

def check_cold_chain(state: BioMaterialState):
    state['validation_steps'].append('Cold Chain Verfication')
    return state

graph = StateGraph(BioMaterialState)
graph.add_node('compliance', validate_compliance)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()
