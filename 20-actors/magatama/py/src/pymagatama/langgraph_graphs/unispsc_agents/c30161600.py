from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CeilingSpecState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: CeilingSpecState):
    errors = []
    if state['specifications'].get('fire_rating') != 'Class A':
        errors.append('Fire rating does not meet Class A safety standard')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: CeilingSpecState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(CeilingSpecState)
graph.add_node('validate', validate_specs)
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'manual_review': END})
graph.set_entry_point('validate')
graph = graph.compile()