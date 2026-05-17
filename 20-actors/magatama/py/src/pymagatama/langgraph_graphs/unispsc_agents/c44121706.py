from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PencilState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_materials(state: PencilState) -> dict:
    errors = []
    if 'FSC_certified' not in state['spec_data']:
        errors.append('Missing environmental certification')
    if 'lead_hardness' not in state['spec_data']:
        errors.append('Missing hardness grade')
    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}

graph = StateGraph(PencilState)
graph.add_node('validation', validate_materials)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()