from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: TapeState):
    specs = state.get('spec_data', {})
    checks = [specs.get('tensile_strength') > 50, 'iso_9001' in specs.get('certs', [])]
    return {'validation_passed': all(checks), 'error_log': [] if all(checks) else ['Specification mismatch']}

def route_by_validation(state: TapeState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(TapeState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: {'error_log': ['Proceeding to procurement']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()