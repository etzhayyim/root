from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IonMicroscopeState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: IonMicroscopeState):
    errors = []
    if state['specs'].get('voltage', 0) > 100: errors.append('Voltage exceeds safety threshold')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_compliance(state: IonMicroscopeState):
    return 'valid' if state['is_compliant'] else 'manual_review'

graph = StateGraph(IonMicroscopeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_compliance, {'valid': END, 'manual_review': END})
graph.compile()