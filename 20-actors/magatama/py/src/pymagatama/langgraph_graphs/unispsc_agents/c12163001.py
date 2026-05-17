from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CatalystProcurementState(TypedDict):
    material_id: str
    purity: float
    spec_check: bool
    approval_path: List[str]

def validate_purity(state: CatalystProcurementState) -> CatalystProcurementState:
    state['spec_check'] = state['purity'] >= 99.5
    return state

def route_approval(state: CatalystProcurementState) -> str:
    if state['spec_check']:
        return 'approve'
    return 'flag_for_review'

graph = StateGraph(CatalystProcurementState)
graph.add_node('validate', validate_purity)
graph.add_conditional_edges('validate', route_approval, {'approve': END, 'flag_for_review': END})
graph.set_entry_point('validate')
compiled_graph = graph.compile()