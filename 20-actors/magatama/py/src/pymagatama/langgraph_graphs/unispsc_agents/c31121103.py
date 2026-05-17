from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CastState):
    required = ['Material Grade', 'Dimensional Tolerance']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_passed': len(missing) == 0, 'error_log': missing}

def structural_analysis(state: CastState):
    print('Running FEA simulation...')
    return {'validation_passed': True}

graph = StateGraph(CastState)
graph.add_node('validate', validate_specs)
graph.add_node('analysis', structural_analysis)
graph.set_entry_point('validate')
graph.add_edge('validate', 'analysis')
graph.add_edge('analysis', END)
graph = graph.compile()