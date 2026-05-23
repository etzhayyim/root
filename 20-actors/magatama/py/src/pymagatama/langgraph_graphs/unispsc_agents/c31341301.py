from typing import TypedDict
from langgraph.graph import StateGraph, END

class AluminumAssemblyState(TypedDict):
    specs: dict
    validation_status: bool
    error_log: list

def validate_aluminum_specs(state: AluminumAssemblyState):
    required_keys = ['welding_cert', 'alloy_type', 'uv_penetration']
    valid = all(key in state['specs'] for key in required_keys)
    return {'validation_status': valid}

def perform_quality_check(state: AluminumAssemblyState):
    if not state.get('validation_status'):
        return {'error_log': ['Invalid assembly parameters']}
    return {'error_log': []}

graph = StateGraph(AluminumAssemblyState)
graph.add_node('validate', validate_aluminum_specs)
graph.add_node('quality_check', perform_quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()
