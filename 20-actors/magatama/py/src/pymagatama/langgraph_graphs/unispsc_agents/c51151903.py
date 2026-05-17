from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_status: bool
    is_approved: bool

def check_quality(state: ProcurementState):
    valid = state['purity'] >= 99.0 and state['gmp_status']
    return {'is_approved': valid}

graph_builder = StateGraph(ProcurementState)
graph_builder.add_node('quality_control', check_quality)
graph_builder.set_entry_point('quality_control')
graph_builder.add_edge('quality_control', END)
graph = graph_builder.compile()