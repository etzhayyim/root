from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZafirlukastState(TypedDict):
    purity_level: float
    compliance_cert: bool
    is_approved: bool

def validate_purity(state: ZafirlukastState):
    return {'is_approved': state['purity_level'] >= 99.0 and state['compliance_cert']}

graph = StateGraph(ZafirlukastState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()
