from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    standards_compliant: bool
    approved: bool

def validate_purity(state: ProcurementState):
    if state['purity'] >= 99.0:
        return {'standards_compliant': True}
    return {'standards_compliant': False}

def final_approval(state: ProcurementState):
    return {'approved': state['standards_compliant']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()