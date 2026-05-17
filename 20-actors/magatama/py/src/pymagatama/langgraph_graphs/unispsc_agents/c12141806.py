from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    batch_id: str
    purity_level: float
    status: str
    validation_log: List[str]

def validate_purity(state: CatalystState) -> CatalystState:
    if state['purity_level'] < 0.99:
        state['status'] = 'REJECTED'
        state['validation_log'].append('Purity below industry standard')
    else:
        state['status'] = 'VALIDATED'
        state['validation_log'].append('Purity check passed')
    return state

def route_to_storage(state: CatalystState) -> str:
    return 'END' if state['status'] == 'VALIDATED' else 'END'

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()