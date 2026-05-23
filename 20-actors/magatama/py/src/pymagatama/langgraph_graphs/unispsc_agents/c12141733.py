from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    material_id: str
    purity: float
    inspection_status: str
    compliance_checks: Annotated[List[str], operator.add]

def validate_purity(state: ResinState) -> ResinState:
    if state['purity'] < 0.999:
        state['inspection_status'] = 'REJECTED'
        state['compliance_checks'].append('purity_too_low')
    else:
        state['inspection_status'] = 'PASSED'
    return state

def perform_export_check(state: ResinState) -> ResinState:
    state['compliance_checks'].append('dual_use_review_complete')
    return state

graph = StateGraph(ResinState)
graph.add_node('validate', validate_purity)
graph.add_node('export_check', perform_export_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
