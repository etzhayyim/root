from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    has_storage_logs: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.5
    return 'check_storage'

def check_storage(state: ProcurementState):
    if state['approved'] and state['has_storage_logs']:
        return 'final'
    state['approved'] = False
    return 'final'

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_purity)
workflow.add_node('check_storage', check_storage)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'check_storage')
workflow.add_edge('check_storage', END)
graph = workflow.compile()