from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WaveGenState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WaveGenState):
    errors = []
    if state['specs'].get('frequency_range', 0) <= 0:
        errors.append('Invalid frequency range')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: WaveGenState):
    return 'compliant' if state['is_compliant'] else 'review'

graph = StateGraph(WaveGenState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'review': END})
