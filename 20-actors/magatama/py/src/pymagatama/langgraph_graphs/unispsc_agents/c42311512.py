from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_medical_standards(state: ProcurementState):
    errors = []
    if 'regulatory_id' not in state['spec_data']:
        errors.append('Missing regulatory certification ID')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_standards)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
