from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity_level: float
    surface_area: float
    validation_log: List[str]
    is_approved: bool

def validate_carrier(state: CatalystState) -> CatalystState:
    if state['purity_level'] < 99.5:
        state['validation_log'].append('Purity below 99.5 percent')
        state['is_approved'] = False
    else:
        state['is_approved'] = True
    return state

def check_stability(state: CatalystState) -> CatalystState:
    if state['is_approved'] and state['surface_area'] > 300:
        state['validation_log'].append('High surface area validation passed')
    return state

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_carrier)
graph.add_node('check', check_stability)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
compile_graph = graph.compile()
