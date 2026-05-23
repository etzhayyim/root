from typing import TypedDict
from langgraph.graph import StateGraph, END
class PharmaState(TypedDict):
    purity: float
    has_gmp: bool
    is_approved: bool
def validate_purity(state: PharmaState):
    state['is_approved'] = state['purity'] >= 99.0 and state['has_gmp']
    return {'is_approved': state['is_approved']}
workflow = StateGraph(PharmaState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
