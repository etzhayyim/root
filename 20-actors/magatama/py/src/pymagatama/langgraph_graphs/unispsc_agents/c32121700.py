from typing import TypedDict
from langgraph.graph import StateGraph, END

class ComponentState(TypedDict):
    part_data: dict
    validation_results: list
    is_compliant: bool

def validate_part(state: ComponentState):
    data = state['part_data']
    results = []
    if 'rohs_status' not in data: results.append('Missing RoHS')
    if 'msl' not in data: results.append('Missing MSL')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def route_by_compliance(state: ComponentState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(ComponentState)
graph.add_node('validate', validate_part)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'manual_review': END})
graph.compile()