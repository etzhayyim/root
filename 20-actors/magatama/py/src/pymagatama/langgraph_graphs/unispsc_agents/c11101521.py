from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    purity_level: float
    impurity_report: dict
    is_approved: bool

def validate_purity(state: MineralState) -> MineralState:
    # Logic for purity threshold validation
    state['is_approved'] = state['purity_level'] >= 99.9
    return state

def check_impurities(state: MineralState) -> MineralState:
    # Logic for impurity profile analysis
    if not state.get('impurity_report'):
        state['is_approved'] = False
    return state

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_impurities', check_impurities)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_impurities')
graph.add_edge('check_impurities', END)
graph = graph.compile()
