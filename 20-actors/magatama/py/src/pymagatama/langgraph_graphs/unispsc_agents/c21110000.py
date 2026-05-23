from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: EquipmentState):
    errors = []
    if state['specifications'].get('noise_level_db', 0) > 95:
        errors.append('Noise level exceeds safety limits')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: EquipmentState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
