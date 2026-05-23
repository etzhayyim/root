from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity: float
    has_sds: bool
    approved: bool

def validate_chemical(state: ChemicalProcurementState):
    is_pure = state['purity'] >= 0.99
    return {'approved': is_pure and state['has_sds']}

workflow = StateGraph(ChemicalProcurementState)
workflow.add_node('validate', validate_chemical)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
