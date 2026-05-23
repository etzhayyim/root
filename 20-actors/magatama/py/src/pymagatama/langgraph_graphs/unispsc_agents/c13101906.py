from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity_level: float
    inspection_results: List[str]
    approved: bool

def validate_purity(state: MineralState) -> MineralState:
    if state.get('purity_level', 0) >= 95.0:
        state['inspection_results'].append('Purity check passed')
    else:
        state['inspection_results'].append('Purity check failed')
    return state

def check_compliance(state: MineralState) -> MineralState:
    if 'Purity check passed' in state['inspection_results']:
        state['approved'] = True
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
