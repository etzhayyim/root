from typing import TypedDict
from langgraph.graph import StateGraph, END

class BlanketState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_materials(state: BlanketState):
    # Business logic for blanket material compliance
    state['validation_passed'] = 'fire_retardant' in state['spec_data']
    return state

def approval_step(state: BlanketState):
    return state

graph = StateGraph(BlanketState)
graph.add_node('validate', validate_materials)
graph.add_node('approval', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()