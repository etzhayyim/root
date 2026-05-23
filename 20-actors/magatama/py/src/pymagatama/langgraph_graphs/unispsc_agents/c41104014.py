from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    approved: bool

def validate_certification(state: ProcurementState):
    cert = state['spec_data'].get('sterile_certification')
    return {'approved': cert is not None}

def process_logistics(state: ProcurementState):
    return {'approved': state['approved']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_certification)
graph.add_node('logistics', process_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()
