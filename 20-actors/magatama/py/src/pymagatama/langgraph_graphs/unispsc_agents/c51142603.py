from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    is_approved: bool

def validate_regulatory_docs(state: ProcurementState):
    required = ['gmp_cert', 'narcotics_license']
    state['is_approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

def route_procurement(state: ProcurementState):
    return 'validate' if state['is_approved'] is None else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_regulatory_docs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
