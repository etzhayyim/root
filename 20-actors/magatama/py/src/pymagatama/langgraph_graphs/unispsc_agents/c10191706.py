from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    capacity: float
    moisture: float
    pest_free: bool
    log: List[str]

def validate_capacity(state: StorageState) -> StorageState:
    if state['capacity'] > 0:
        state['log'].append('Capacity validated.')
    return state

def check_integrity(state: StorageState) -> StorageState:
    if state['moisture'] < 12.0 and state['pest_free']:
        state['log'].append('Integrity check passed.')
    else:
        state['log'].append('Integrity alert: Check environment.')
    return state

graph = StateGraph(StorageState)
graph.add_node('capacity', validate_capacity)
graph.add_node('integrity', check_integrity)
graph.set_entry_point('capacity')
graph.add_edge('capacity', 'integrity')
graph.add_edge('integrity', END)
graph = graph.compile()
