from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningState(TypedDict):
    equipment_id: str
    inspection_results: List[str]
    status: str

def validate_spec(state: MiningState) -> MiningState:
    state['inspection_results'].append('Specification validation completed.')
    state['status'] = 'VALIDATED'
    return state

def perform_safety_check(state: MiningState) -> MiningState:
    state['inspection_results'].append('Safety check passed for mining site usage.')
    return state

graph = StateGraph(MiningState)
graph.add_node('validate', validate_spec)
graph.add_node('safety', perform_safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()