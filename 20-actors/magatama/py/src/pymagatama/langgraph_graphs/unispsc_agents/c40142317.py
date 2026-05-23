from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeElbowState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list

def validate_specs(state: PipeElbowState):
    specs = state['spec_data']
    required = ['material', 'pressure_rating', 'size']
    missing = [f for f in required if f not in specs]
    return {'validation_result': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: PipeElbowState):
    return 'valid' if state['validation_result'] else 'invalid'

graph = StateGraph(PipeElbowState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
