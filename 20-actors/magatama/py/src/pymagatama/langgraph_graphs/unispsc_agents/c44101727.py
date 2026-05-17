from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrinterStandState(TypedDict):
    weight_capacity: float
    has_casters: bool
    compliant: bool

def validate_load_capacity(state: PrinterStandState):
    state['compliant'] = state['weight_capacity'] >= 50.0
    return state

workflow = StateGraph(PrinterStandState)
workflow.add_node('validation', validate_load_capacity)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()