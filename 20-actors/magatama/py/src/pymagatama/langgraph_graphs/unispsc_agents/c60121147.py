from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_paper_spec(state: PaperProcurementState):
    errors = []
    if state['specifications'].get('basis_weight_gsm', 0) < 80:
        errors.append('Weight too low for professional glossy output')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def approve_procurement(state: PaperProcurementState):
    return {'is_approved': True}

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_paper_spec)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.set_entry_point('validate')
graph.add_edge('approve', END)
graph = graph.compile()
