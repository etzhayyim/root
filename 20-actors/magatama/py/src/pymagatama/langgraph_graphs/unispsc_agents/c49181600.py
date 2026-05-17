from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TargetSystemState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_logs: List[str]

def validate_specs(state: TargetSystemState):
    specs = state.get('specs', {})
    valid = specs.get('impact_resistance') > 1000
    return {'is_compliant': valid, 'validation_logs': ['Impact test verified' if valid else 'Impact test failed']}

def route_by_compliance(state: TargetSystemState):
    return 'compliant_path' if state['is_compliant'] else 'reject_path'

graph = StateGraph(TargetSystemState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant_path': END, 'reject_path': END})
graph = graph.compile()