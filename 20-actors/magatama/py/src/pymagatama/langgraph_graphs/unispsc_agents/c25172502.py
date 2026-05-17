from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TubeProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: TubeProcurementState):
    errors = []
    if not state['spec_data'].get('valve_type'):
        errors.append('Valve type is missing.')
    return {'validation_errors': errors}

def decision_node(state: TubeProcurementState):
    return 'END' if not state['validation_errors'] else 'END'

graph = StateGraph(TubeProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('decision', decision_node)
graph.add_edge('validate', 'decision')
graph.set_entry_point('validate')
graph.set_finish_point('decision')
procurement_graph = graph.compile()