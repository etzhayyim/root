from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity: float
    safety_check_passed: bool
    log: List[str]

def validate_purity(state: CatalystState) -> CatalystState:
    if state['purity'] >= 99.9:
        state['log'].append('Purity validation passed')
        state['safety_check_passed'] = True
    else:
        state['log'].append('Purity validation failed')
        state['safety_check_passed'] = False
    return state

def route_by_safety(state: CatalystState) -> str:
    return 'process' if state['safety_check_passed'] else 'END'

def process_catalyst(state: CatalystState) -> CatalystState:
    state['log'].append('Proceeding to industrial chemical processing workflow')
    return state

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_catalyst)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()