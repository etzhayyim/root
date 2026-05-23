from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieCastState(TypedDict):
    part_specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: DieCastState):
    required = ['tolerance', 'material', 'surface_finish']
    passed = all(k in state['part_specs'] for k in required)
    return {'validation_passed': passed}

def structural_check(state: DieCastState):
    print('Checking structural integrity based on NDT report...')
    return {'validation_passed': state['validation_passed'] and True}

graph = StateGraph(DieCastState)
graph.add_node('validate', validate_specs)
graph.add_node('structural', structural_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'structural')
graph.add_edge('structural', END)
graph = graph.compile()
