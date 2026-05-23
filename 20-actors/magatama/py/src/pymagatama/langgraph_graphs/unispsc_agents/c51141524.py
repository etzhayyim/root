from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class ProcureState(TypedDict):
    material: str
    purity: float
    has_license: bool
    is_approved: bool
def validate_compliance(state: ProcureState):
    state['is_approved'] = state['purity'] >= 99.0 and state['has_license']
    return state
def route_procurement(state: ProcureState):
    return 'approved' if state['is_approved'] else 'rejected'
graph = StateGraph(ProcureState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
