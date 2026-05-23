from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    safety_certs: List[str]
    approved: bool

def validate_safety(state: ProcurementState) -> dict:
    required = ['OEKO-TEX', 'Flame-Retardant-Compliance']
    approved = all(cert in state['safety_certs'] for cert in required)
    return {'approved': approved}

def finalize_order(state: ProcurementState) -> dict:
    return {'approved': True if state['approved'] else False}

graph = StateGraph(ProcurementState)
graph.add_node('validate_safety', validate_safety)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate_safety', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate_safety')
compiled_graph = graph.compile()
