from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: bool
    approved: bool

def validate_batch(state: ProcurementState):
    state['approved'] = state['purity_level'] > 99.0 and state['compliance_docs']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
