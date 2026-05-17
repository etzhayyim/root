from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class SuggestionBoxState(TypedDict):
    material: str
    lock_type: str
    is_compliant: bool

def validate_material(state: SuggestionBoxState):
    state['is_compliant'] = state['material'] in ['Steel', 'Aluminum', 'ABS Plastic']
    return state

def validate_locking(state: SuggestionBoxState):
    if state['is_compliant']:
        state['is_compliant'] = state['lock_type'] == 'Keyed'
    return state

graph = StateGraph(SuggestionBoxState)
graph.add_node('validate_material', validate_material)
graph.add_node('validate_locking', validate_locking)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'validate_locking')
graph.add_edge('validate_locking', END)
graph = graph.compile()