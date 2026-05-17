from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    material_id: str
    viscosity: float
    safety_clearance: bool
    steps: List[str]

def validate_chemical_safety(state: AdhesiveState) -> AdhesiveState:
    # Logic to verify SDS/MSDS compatibility
    state['safety_clearance'] = True
    state['steps'].append('Safety validation complete')
    return state

def check_viscosity_specs(state: AdhesiveState) -> AdhesiveState:
    if state['viscosity'] > 500:
        state['steps'].append('Viscosity within high-performance range')
    return state

graph = StateGraph(AdhesiveState)
graph.add_node('validate', validate_chemical_safety)
graph.add_node('check', check_viscosity_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
app = graph.compile()