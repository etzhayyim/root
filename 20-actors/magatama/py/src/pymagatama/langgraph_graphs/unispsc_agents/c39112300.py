from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingSpecState(TypedDict):
    item_id: str
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: LightingSpecState):
    errors = []
    if not state['spec_data'].get('load_capacity'):
        errors.append('Missing mandatory load capacity')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: LightingSpecState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(LightingSpecState)
graph.add_node('validate', validate_specs)
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'manual_review': END})
graph.set_entry_point('validate')
graph = graph.compile()
