from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    purity_level: float
    particle_distribution: List[float]
    compliance_check: bool
    error_log: List[str]

def validate_chemical_purity(state: MetalPowderState) -> MetalPowderState:
    if state['purity_level'] < 99.9:
        state['error_log'].append('Purity level below industrial standard.')
        state['compliance_check'] = False
    return state

def check_particle_specs(state: MetalPowderState) -> MetalPowderState:
    if not state['particle_distribution']:
        state['error_log'].append('Invalid particle size distribution.')
        state['compliance_check'] = False
    return state

graph = StateGraph(MetalPowderState)
graph.add_node('validate_purity', validate_chemical_purity)
graph.add_node('validate_particles', check_particle_specs)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'validate_particles')
graph.add_edge('validate_particles', END)
graph = graph.compile()
