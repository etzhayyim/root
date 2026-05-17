from typing import TypedDict
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    capacity: float
    material: str
    is_compliant: bool

def validate_specs(state: StorageState) -> StorageState:
    if state['capacity'] > 0 and state['material'] == 'steel':
        state['is_compliant'] = True
    else:
        state['is_compliant'] = False
    return state

graph = StateGraph(StorageState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()