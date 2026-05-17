from typing import TypedDict
from langgraph.graph import StateGraph, END

class APIProcurementState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_check: bool

def validate_quality(state: APIProcurementState):
    return {'compliance_check': state['purity'] >= 99.0 and state['gmp_certified']}

graph = StateGraph(APIProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()