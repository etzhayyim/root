from typing import TypedDict
from langgraph.graph import StateGraph, END

class SterilizationState(TypedDict):
    kit_id: str
    validation_status: str
    log_reduction_val: float

def validate_batch(state: SterilizationState):
    # Business logic for biological kit validation
    if state['log_reduction_val'] >= 6.0:
        return {'validation_status': 'PASS'}
    return {'validation_status': 'FAIL'}

def graph_build():
    graph = StateGraph(SterilizationState)
    graph.add_node('validate', validate_batch)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = graph_build()
