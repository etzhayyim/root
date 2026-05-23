from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity: float
    temp_log_compliant: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_storage(state: ProcurementState):
    if not state['temp_log_compliant']:
        state['approved'] = False
    return state

graph_builder = StateGraph(ProcurementState)
graph_builder.add_node('validate', validate_purity)
graph_builder.add_node('storage_check', check_storage)
graph_builder.add_edge('validate', 'storage_check')
graph_builder.add_edge('storage_check', END)
graph_builder.set_entry_point('validate')
graph = graph_builder.compile()
