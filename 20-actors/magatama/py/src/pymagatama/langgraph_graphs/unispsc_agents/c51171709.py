from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    cfu_count: float
    purity_pct: float
    temp_log: list
    status: str

def validate_batch(state: ProcurementState):
    if state['cfu_count'] < 1e9: return {'status': 'rejected'}
    return {'status': 'approved'}

def graph_setup():
    graph = StateGraph(ProcurementState)
    graph.add_node('validate', validate_batch)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = graph_setup()
