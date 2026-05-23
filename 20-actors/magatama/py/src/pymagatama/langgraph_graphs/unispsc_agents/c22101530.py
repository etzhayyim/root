from typing import TypedDict
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: FastenerState):
    # Business logic for fastener spec validation
    tensile = state['specs'].get('tensile_strength', 0)
    return {'approved': tensile > 500}

def route_by_approval(state: FastenerState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph.compile()
