from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PaperProcurementState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_paper_specs(state: PaperProcurementState):
    errors = []
    if state['specifications'].get('gsm', 0) < 190:
        errors.append('Basis weight too low for professional watercolor.')
    return {'validation_errors': errors}

def decision_node(state: PaperProcurementState):
    return 'APPROVED' if not state['validation_errors'] else 'REJECTED'

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_paper_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
