from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeInsertState(TypedDict):
    material: str
    pressure_class: int
    certified: bool

def validate_specs(state: PipeInsertState):
    is_valid = state['pressure_class'] > 0 and state['material'] != ''
    return {'certified': is_valid}

def approval_node(state: PipeInsertState):
    return {'certified': True}

graph = StateGraph(PipeInsertState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph.compile()