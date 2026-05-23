from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    has_gmp: bool
    passed_inspection: bool

def validate_api_specs(state: PharmState):
    if state['purity'] >= 99.0 and state['has_gmp']:
        return {'passed_inspection': True}
    return {'passed_inspection': False}

def route_by_inspection(state: PharmState):
    return 'process' if state['passed_inspection'] else 'reject'

graph = StateGraph(PharmState)
graph.add_node('validate', validate_api_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
