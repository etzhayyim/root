from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: list
    is_approved: bool

def validate_purity(state: ProcurementState):
    return {'is_approved': state['purity'] >= 99.0}

def check_docs(state: ProcurementState):
    return {'compliance_docs': ['CoA', 'MSDS']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('docs', check_docs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'docs')
graph.add_edge('docs', END)
app = graph.compile()