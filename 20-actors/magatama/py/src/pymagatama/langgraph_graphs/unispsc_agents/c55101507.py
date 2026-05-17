from typing import TypedDict
from langgraph.graph import StateGraph, END

class BookProcurementState(TypedDict):
    specs: dict
    approved: bool

def validate_safety_compliance(state: BookProcurementState):
    compliance = state['specs'].get('safety_standard', False)
    return {'approved': bool(compliance)}

graph = StateGraph(BookProcurementState)
graph.add_node('validate', validate_safety_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()