from typing import TypedDict
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    capacity: int
    encryption: bool
    verified: bool

def validate_specs(state: StorageState):
    state['verified'] = state['capacity'] > 0 and state['encryption'] is True
    return state

workflow = StateGraph(StorageState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()