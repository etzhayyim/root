from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_items: List[dict]
    validation_errors: List[str]
    is_compliant: bool

def validate_curriculum_standard(state: ProcurementState):
    errors = []
    for item in state['material_items']:
        if 'curriculum_alignment' not in item:
            errors.append(f'Missing alignment for {item.get('name')}')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approve_procurement(state: ProcurementState):
    return {'is_compliant': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_curriculum_standard)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.set_entry_point('validate')
graph.set_finish_point('approve')
graph = graph.compile()