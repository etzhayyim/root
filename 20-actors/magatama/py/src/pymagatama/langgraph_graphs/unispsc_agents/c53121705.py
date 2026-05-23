from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentCaseState(TypedDict):
    case_spec: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: EquipmentCaseState):
    errors = []
    if state['case_spec'].get('ip_rating', 0) < 65:
        errors.append('Insufficient IP rating for equipment protection.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(EquipmentCaseState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
