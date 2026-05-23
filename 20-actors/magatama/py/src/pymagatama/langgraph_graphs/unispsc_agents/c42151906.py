from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    concentration: float
    compliance_checked: bool

def validate_pharmaceutical(state: ProcurementState):
    state['compliance_checked'] = state['concentration'] > 0 and state['concentration'] <= 2.2
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pharmaceutical)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
