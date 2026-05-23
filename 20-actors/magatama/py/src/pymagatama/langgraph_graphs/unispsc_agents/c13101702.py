from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    chemical_id: str
    purity_check: float
    separation_steps: List[str]
    hazard_verified: bool

def validate_purity(state: MineralProcessState) -> MineralProcessState:
    if state['purity_check'] < 98.0:
        state['separation_steps'].append('reject_low_purity')
    else:
        state['separation_steps'].append('approve_for_flotation')
    return state

def hazard_verification(state: MineralProcessState) -> MineralProcessState:
    state['hazard_verified'] = True
    return state

graph = StateGraph(MineralProcessState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('hazard_verification', hazard_verification)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'hazard_verification')
graph.add_edge('hazard_verification', END)

compiled_graph = graph.compile()
