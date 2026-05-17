from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TugBoatState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: TugBoatState):
    errors = []
    if state['specs'].get('bollard_pull', 0) < 30:
        errors.append('Insufficient bollard pull for port operations.')
    return {'validation_errors': errors}

def compliance_check(state: TugBoatState):
    is_compliant = len(state['validation_errors']) == 0
    return {'approved': is_compliant}

graph = StateGraph(TugBoatState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()