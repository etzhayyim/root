from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintProcurementState(TypedDict):
    voc_level: float
    has_sds: bool
    is_compliant: bool

def validate_chemistry(state: PaintProcurementState):
    state['is_compliant'] = state['voc_level'] < 250 and state['has_sds']
    return state

graph = StateGraph(PaintProcurementState)
graph.add_node('validate', validate_chemistry)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()