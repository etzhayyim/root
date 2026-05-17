from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    purity: float
    particle_mesh: int
    analysis_report: str
    is_compliant: bool

def validate_purity(state: MineralState) -> MineralState:
    state['is_compliant'] = state['purity'] >= 99.5
    return state

def check_particle_size(state: MineralState) -> MineralState:
    if state['particle_mesh'] < 200:
        state['is_compliant'] = False
    return state

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_size', check_particle_size)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_size')
graph.add_edge('check_size', END)
graph = graph.compile()