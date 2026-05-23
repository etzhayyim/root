from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity: float
    origin: str
    validation_logs: List[str]
    is_compliant: bool

def validate_purity(state: MineralState) -> MineralState:
    if state['purity'] >= 0.95:
        state['validation_logs'].append('Purity check passed')
        state['is_compliant'] = True
    else:
        state['validation_logs'].append('Purity below threshold')
        state['is_compliant'] = False
    return state

def check_origin(state: MineralState) -> MineralState:
    if state['origin'] in ['Domestic', 'Approved_Partner']:
        state['validation_logs'].append('Origin verified')
    else:
        state['validation_logs'].append('Origin risk detected')
        state['is_compliant'] = False
    return state

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_origin', check_origin)
graph.add_edge('validate_purity', 'check_origin')
graph.add_edge('check_origin', END)
graph.set_entry_point('validate_purity')
compiled_graph = graph.compile()
