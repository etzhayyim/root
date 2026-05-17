from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrakeSystemState(TypedDict):
    pressure_rating: float
    safety_certification: str
    is_compliant: bool

def validate_specs(state: BrakeSystemState):
    compliant = state['pressure_rating'] > 0 and 'ISO' in state['safety_certification']
    return {'is_compliant': compliant}

def route_by_compliance(state: BrakeSystemState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(BrakeSystemState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END, 'reject': END})
graph.compile()