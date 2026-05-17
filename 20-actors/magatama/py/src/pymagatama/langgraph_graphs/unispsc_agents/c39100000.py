from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: LightingState):
    errors = []
    if state['specs'].get('wattage', 0) > 1000:
        errors.append('Wattage exceeds safety thresholds')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: LightingState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()