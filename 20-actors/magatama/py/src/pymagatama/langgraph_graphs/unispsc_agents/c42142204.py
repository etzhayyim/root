from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HydrotherapyState(TypedDict):
    product_id: str
    safety_certs: List[str]
    spec_compliance: bool

def validate_certification(state: HydrotherapyState):
    required = ['ISO13485', 'CE_Medical', 'FDA_Class_I']
    compliance = all(item in state['safety_certs'] for item in required)
    return {'spec_compliance': compliance}

def approve_procurement(state: HydrotherapyState):
    return 'Approved' if state['spec_compliance'] else 'Rejected'

graph = StateGraph(HydrotherapyState)
graph.add_node('validate', validate_certification)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()