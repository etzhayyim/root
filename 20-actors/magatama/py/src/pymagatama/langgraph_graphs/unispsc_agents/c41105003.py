from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SieveState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_mesh_size(state: SieveState):
    errors = []
    if 'mesh_size' not in state['specifications']:
        errors.append('Missing mandatory field: mesh_size')
    return {'validation_errors': errors}

def check_compliance(state: SieveState):
    compliant = len(state['validation_errors']) == 0
    return {'is_compliant': compliant}

graph = StateGraph(SieveState)
graph.add_node('validate', validate_mesh_size)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
