from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CatalystState(TypedDict):
    material_id: str
    purity_level: float
    inspection_status: List[str]
    approved: bool

def validate_purity(state: CatalystState) -> CatalystState:
    if state['purity_level'] >= 99.9:
        state['inspection_status'].append('Purity Verified')
    else:
        state['inspection_status'].append('Purity Failed')
    return state

def check_compliance(state: CatalystState) -> CatalystState:
    if 'Purity Verified' in state['inspection_status']:
        state['approved'] = True
    return state

workflow = StateGraph(CatalystState)
workflow.add_node('validate', validate_purity)
workflow.add_node('compliance', check_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()