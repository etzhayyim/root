from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity: float
    compliance_checked: bool

def validate_purity(state: ProcurementState):
    if state['purity'] < 0.99:
        raise ValueError('Purity below pharmaceutical grade')
    return {'compliance_checked': True}

def finalize_order(state: ProcurementState):
    return {'status': 'approved'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()