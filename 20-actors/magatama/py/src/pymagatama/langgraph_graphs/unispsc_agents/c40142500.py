from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrapState(TypedDict):
    pressure_rating: int
    material_compliance: bool
    is_validated: bool

def validate_specs(state: TrapState):
    state['is_validated'] = state['pressure_rating'] > 150 and state['material_compliance']
    return state

def route_by_spec(state: TrapState):
    return 'valid' if state['is_validated'] else 'reject'

graph = StateGraph(TrapState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
