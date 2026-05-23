from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    purity_level: float
    origin: str
    is_compliant: bool
    log: List[str]

def validate_purity(state: MineralState) -> MineralState:
    state['is_compliant'] = state['purity_level'] >= 99.5
    state['log'].append(f'Purity check: {state["purity_level"]} - Valid: {state["is_compliant"]}')
    return state

def check_origin(state: MineralState) -> MineralState:
    state['log'].append(f'Origin validation: {state["origin"]}')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_origin', check_origin)
graph.add_edge('validate_purity', 'check_origin')
graph.add_edge('check_origin', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()
