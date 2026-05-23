from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FaucetSpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material(state: FaucetSpecState):
    errors = []
    if 'material' not in state['spec_data']:
        errors.append('Missing material composition')
    return {'validation_errors': errors}

def check_compliance(state: FaucetSpecState):
    compliant = len(state['validation_errors']) == 0
    return {'is_compliant': compliant}

graph = StateGraph(FaucetSpecState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
