from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    juice_data: dict
    validation_results: dict

def validate_quality(state: ProcessingState):
    metrics = state['juice_data'].get('metrics', {})
    is_valid = metrics.get('brix', 0) > 10 and metrics.get('ph', 0) < 4.5
    return {'validation_results': {'passed': is_valid}}

def route_by_validation(state: ProcessingState):
    return 'passed' if state['validation_results']['passed'] else END

graph = StateGraph(ProcessingState)
graph.add_node('quality_check', validate_quality)
graph.add_conditional_edges('quality_check', route_by_validation, {'passed': END})
graph.set_entry_point('quality_check')
graph = graph.compile()