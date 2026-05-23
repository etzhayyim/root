from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EarProtectionState(TypedDict):
    product_id: str
    nrr_rating: float
    compliance_docs: List[str]
    approved: bool

def validate_safety_standards(state: EarProtectionState):
    state['approved'] = state['nrr_rating'] >= 20 and len(state['compliance_docs']) > 0
    return state

graph = StateGraph(EarProtectionState)
graph.add_node('validate', validate_safety_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

compile_graph = graph.compile()
