from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RopeLightState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: RopeLightState):
    errors = []
    if not state['spec_sheet'].get('IP_rating'):
        errors.append('Missing IP rating for outdoor safety compliance')
    if state['spec_sheet'].get('voltage') not in ['110V', '220V']:
        errors.append('Unsupported voltage specification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(RopeLightState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
