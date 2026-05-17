from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity: float
    has_sds: bool
    is_approved: bool

def validate_copper_sulfate(state: ChemicalProcurementState):
    # Business logic for Copper Sulfate validation
    if state['purity'] >= 98.0 and state['has_sds']:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validation', validate_copper_sulfate)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()