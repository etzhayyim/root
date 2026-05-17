from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WasherState(TypedDict):
    specs: dict
    validated: bool
    error_log: List[str]

def validate_material(state: WasherState) -> WasherState:
    material = state.get('specs', {}).get('material', '')
    if not material: state['error_log'].append('Missing material')
    return state

def check_load(state: WasherState) -> WasherState:
    if state.get('specs', {}).get('load', 0) <= 0:
        state['error_log'].append('Invalid load capacity')
    else:
        state['validated'] = True
    return state

graph = StateGraph(WasherState)
graph.add_node('validate', validate_material)
graph.add_node('load_check', check_load)
graph.add_edge('validate', 'load_check')
graph.add_edge('load_check', END)
graph.set_entry_point('validate')
graph = graph.compile()