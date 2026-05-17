from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class CalligraphyState(TypedDict):
    spec_data: dict
    is_validated: bool

def validate_nib_specification(state: CalligraphyState):
    nib = state['spec_data'].get('nib_material', '')
    return {'is_validated': nib in ['metal', 'nylon', 'natural_hair']}

def quality_check(state: CalligraphyState):
    return {'is_validated': state['is_validated'] and state['spec_data'].get('ink_type') == 'archival'}

graph = StateGraph(CalligraphyState)
graph.add_node('validate_nib', validate_nib_specification)
graph.add_node('qc', quality_check)
graph.add_edge('validate_nib', 'qc')
graph.add_edge('qc', END)
graph.set_entry_point('validate_nib')
graph = graph.compile()