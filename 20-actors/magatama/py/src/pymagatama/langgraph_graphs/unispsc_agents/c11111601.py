from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity: float
    origin: str
    validation_passed: bool
    error_logs: List[str]

def validate_purity(state: MineralState) -> MineralState:
    if state['purity'] < 95.0:
        state['validation_passed'] = False
        state['error_logs'].append('Purity below 95% threshold')
    else:
        state['validation_passed'] = True
    return state

def check_sanctions(state: MineralState) -> MineralState:
    if state['origin'] in ['RestrictedRegionA', 'RestrictedRegionB']:
        state['validation_passed'] = False
        state['error_logs'].append('Origin under export sanction')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('sanctions', check_sanctions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sanctions')
graph.add_edge('sanctions', END)
compiled_graph = graph.compile()