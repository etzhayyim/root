from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ArborState(TypedDict):
    arbor_specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_arbor_specs(state: ArborState):
    specs = state['arbor_specs']
    errors = []
    if 'runout_tolerance' not in specs: errors.append('Missing runout tolerance')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: ArborState):
    return 'process' if state['validation_passed'] else END

def perform_cad_check(state: ArborState):
    print('Performing mechanical CAD validation for arbor dimensions...')
    return state

graph = StateGraph(ArborState)
graph.add_node('validate', validate_arbor_specs)
graph.add_node('process', perform_cad_check)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
