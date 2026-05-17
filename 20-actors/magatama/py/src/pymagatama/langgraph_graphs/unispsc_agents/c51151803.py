from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NadololState(TypedDict):
    batch_id: str
    purity_level: float
    has_coa: bool
    compliant: bool

def validate_quality(state: NadololState) -> NadololState:
    state['compliant'] = state['purity_level'] >= 99.0 and state['has_coa']
    return state

def check_stability(state: NadololState) -> NadololState:
    if state['compliant']:
        print(f'Batch {state['batch_id']} cleared for clinical distribution.')
    return state

graph = StateGraph(NadololState)
graph.add_node('validate', validate_quality)
graph.add_node('stability', check_stability)
graph.set_entry_point('validate')
graph.add_edge('validate', 'stability')
graph.add_edge('stability', END)
graph = graph.compile()