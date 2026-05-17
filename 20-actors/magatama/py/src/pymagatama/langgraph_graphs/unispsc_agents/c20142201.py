from typing import TypedDict
from langgraph.graph import StateGraph, END

class HoseState(TypedDict):
    pressure_rating: int
    fluid_type: str
    is_compliant: bool

def validate_specs(state: HoseState):
    state['is_compliant'] = state['pressure_rating'] > 0 and state['fluid_type'] is not None
    return state

def route_verification(state: HoseState):
    return 'compliant_node' if state['is_compliant'] else 'reject_node'

graph = StateGraph(HoseState)
graph.add_node('validate', validate_specs)
graph.add_entry_point('validate')
graph.add_conditional_edges('validate', route_verification, {'compliant_node': END, 'reject_node': END})
graph.compile()