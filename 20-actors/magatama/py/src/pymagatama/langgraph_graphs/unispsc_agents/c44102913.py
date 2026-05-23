from typing import TypedDict
from langgraph.graph import StateGraph, END

class DestructionState(TypedDict):
    device_id: str
    security_level: str
    is_verified: bool

def validate_specs(state: DestructionState):
    state['is_verified'] = state['security_level'] in ['O-1', 'O-2', 'O-3']
    return state

def log_destruction(state: DestructionState):
    if state['is_verified']:
        print(f'Device {state["device_id"]} passed security verification.')
    return state

graph = StateGraph(DestructionState)
graph.add_node('validate', validate_specs)
graph.add_node('log', log_destruction)
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph.set_entry_point('validate')
graph = graph.compile()
