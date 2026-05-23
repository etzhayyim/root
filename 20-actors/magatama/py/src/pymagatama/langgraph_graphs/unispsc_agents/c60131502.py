from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReedProcurementState(TypedDict):
    reed_grade: str
    quality_check: bool
    approved: bool

def validate_reed_specs(state: ReedProcurementState):
    state['quality_check'] = state['reed_grade'] in ['Professional', 'Student']
    return state

def approval_step(state: ReedProcurementState):
    state['approved'] = state['quality_check']
    return state

graph = StateGraph(ReedProcurementState)
graph.add_node('validate', validate_reed_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
