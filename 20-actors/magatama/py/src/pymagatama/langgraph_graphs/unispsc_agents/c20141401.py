from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatExchangerState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: HeatExchangerState):
    errors = []
    if 'pressure_rating' not in state['spec_data']: errors.append('Pressure rating missing')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: HeatExchangerState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(HeatExchangerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END, 'reject': END})