from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubingState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_tubing_specs(state: TubingState):
    required = ['sterilization_method', 'luer_lock_compatibility']
    missing = [f for f in required if f not in state['spec_data']]
    is_compliant = len(missing) == 0
    return {'is_compliant': is_compliant, 'validation_log': [f'Missing: {missing}'] if missing else ['Specs valid']}

def route_by_compliance(state: TubingState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(TubingState)
graph.add_node('validate', validate_tubing_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'reject': END})
graph = graph.compile()