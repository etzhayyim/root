from typing import TypedDict
from langgraph.graph import StateGraph, END
class PharmaState(TypedDict):
    product_name: str
    purity_level: float
    compliance_checked: bool
    approved: bool
def validate_quality(state: PharmaState):
    state['compliance_checked'] = state['purity_level'] >= 99.0
    return state
def final_approval(state: PharmaState):
    state['approved'] = state['compliance_checked']
    return state
graph = StateGraph(PharmaState)
graph.add_node('validate', validate_quality)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
