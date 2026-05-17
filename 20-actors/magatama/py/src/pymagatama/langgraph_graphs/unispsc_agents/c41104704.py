from typing import TypedDict
from langgraph.graph import StateGraph, END

class FreezeDryerState(TypedDict):
    part_id: str
    material_spec: str
    is_compatible: bool

def validate_part(state: FreezeDryerState):
    # Business logic for checking component compatibility
    state['is_compatible'] = state['material_spec'] == '316L_SS'
    return state

def route_by_compatibility(state: FreezeDryerState):
    return 'process' if state['is_compatible'] else 'flag_manual_review'

graph = StateGraph(FreezeDryerState)
graph.add_node('validate', validate_part)
graph.add_edge('validate', 'process')
graph.set_entry_point('validate')
graph.set_finish_point('process')
graph.compile()