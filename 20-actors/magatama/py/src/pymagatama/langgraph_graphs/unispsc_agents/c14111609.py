from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    paper_type: str
    gsm: int
    is_acid_free: bool
    validation_errors: List[str]
    approved: bool

def validate_paper_spec(state: PaperProcurementState):
    errors = []
    if state['gsm'] < 60 or state['gsm'] > 120:
        errors.append('GSM outside standard office range')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def decision_node(state: PaperProcurementState):
    return 'approved' if state['approved'] else END

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_paper_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

compiled_graph = graph.compile()