from typing import TypedDict
from langgraph.graph import StateGraph, END

class AS_RS_State(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: AS_RS_State):
    errors = []
    if not state['specs'].get('load_capacity_kg'): errors.append('Missing capacity')
    if not state['specs'].get('safety_certification'): errors.append('Missing safety cert')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: AS_RS_State):
    return 'compliant_node' if state['is_compliant'] else 'reject_node'

graph = StateGraph(AS_RS_State)
graph.add_node('validator', validate_specs)
graph.add_node('compliant_node', lambda x: x)
graph.add_node('reject_node', lambda x: x)
graph.set_entry_point('validator')
graph.add_conditional_edges('validator', route_by_compliance)
graph.add_edge('compliant_node', END)
graph.add_edge('reject_node', END)
graph = graph.compile()