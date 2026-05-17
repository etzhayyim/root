from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

class PaperProcureState(TypedDict):
    spec_requirements: Dict[str, Any]
    validation_results: Dict[str, bool]
    approved: bool

def validate_paper_spec(state: PaperProcureState) -> PaperProcureState:
    # Logic to validate paper specs like GSM and certifications
    gsm = state['spec_requirements'].get('gsm', 0)
    state['validation_results'] = {'gsm_valid': gsm > 0}
    state['approved'] = all(state['validation_results'].values())
    return state

def route_procurement(state: PaperProcureState) -> str:
    return 'approved' if state['approved'] else 'rejected'

workflow = StateGraph(PaperProcureState)
workflow.add_node('validate', validate_paper_spec)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)

graph = workflow.compile()