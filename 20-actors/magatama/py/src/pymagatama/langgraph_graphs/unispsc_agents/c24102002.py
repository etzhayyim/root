from typing import TypedDict
from langgraph.graph import StateGraph, END

class BinHandlerState(TypedDict):
    capacity: float
    safety_check: bool
    is_validated: bool

def validate_specs(state: BinHandlerState):
    state['is_validated'] = state['capacity'] > 0 and state['safety_check']
    return state

def assembly_process(state: BinHandlerState):
    return {'is_validated': True}

graph = StateGraph(BinHandlerState)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assembly_process)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
app = graph.compile()
