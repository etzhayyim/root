from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PaperProductState(TypedDict):
    product_id: str
    spec_requirements: dict
    validation_results: List[str]
    is_compliant: bool

def validate_absorbency(state: PaperProductState) -> PaperProductState:
    req = state.get('spec_requirements', {})
    if req.get('absorbency_rate_g_per_m2', 0) >= 300:
        state['validation_results'].append('Absorbency check passed')
    else:
        state['validation_results'].append('Absorbency check failed')
    return state

def compliance_check(state: PaperProductState) -> str:
    if 'Absorbency check failed' in state['validation_results']:
        return 'fail'
    return 'pass'

graph = StateGraph(PaperProductState)
graph.add_node('validate', validate_absorbency)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()