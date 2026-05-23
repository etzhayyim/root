from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    alloy_data: dict
    validation_result: bool
    compliance_score: float

def validate_alloy_specs(state: CastingState):
    specs = state['alloy_data']
    # Check for critical ferrous thresholds
    is_valid = specs.get('tensile_strength', 0) > 400 and 'certification' in specs
    return {'validation_result': is_valid, 'compliance_score': 0.95 if is_valid else 0.0}

def route_for_quality_check(state: CastingState):
    return 'process_workflow' if state['validation_result'] else END

graph = StateGraph(CastingState)
graph.add_node('validate', validate_alloy_specs)
graph.add_node('process_workflow', lambda s: {'compliance_score': 1.0})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_for_quality_check)
graph.add_edge('process_workflow', END)
graph = graph.compile()
