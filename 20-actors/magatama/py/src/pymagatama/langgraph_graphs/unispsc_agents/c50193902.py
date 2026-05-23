from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PearProcurementState(TypedDict):
    product_id: str
    quality_docs: List[str]
    is_compliant: bool

def validate_quality(state: PearProcurementState):
    state['is_compliant'] = 'certificate_of_analysis' in state['quality_docs']
    return state

def route_procurement(state: PearProcurementState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(PearProcurementState)
graph.add_node('validate', validate_quality)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
