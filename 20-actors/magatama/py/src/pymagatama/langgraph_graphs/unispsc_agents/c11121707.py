from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiCState(TypedDict):
    material_id: str
    purity_level: float
    particle_distribution: List[float]
    is_compliant: bool

def validate_purity(state: SiCState) -> SiCState:
    state['is_compliant'] = state['purity_level'] >= 99.5
    return state

def analyze_particles(state: SiCState) -> SiCState:
    if not state['is_compliant']: return state
    state['is_compliant'] = all(d > 0 for d in state['particle_distribution'])
    return state

graph = StateGraph(SiCState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('analyze_particles', analyze_particles)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'analyze_particles')
graph.add_edge('analyze_particles', END)
app = graph.compile()