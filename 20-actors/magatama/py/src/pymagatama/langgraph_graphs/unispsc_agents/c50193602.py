from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    quality_docs: List[str]
    approved: bool

def validate_quality(state: ProcurementState):
    required = ['lab_report', 'origin_cert', 'sanitary_permit']
    state['approved'] = all(doc in state['quality_docs'] for doc in required)
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
