from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class ProcureState(TypedDict):
    item_name: str
    spec_verified: bool
    vendor_approved: bool
def validate_specs(state: ProcureState):
    state['spec_verified'] = 'gold' in state['item_name'].lower() or 'award' in state['item_name'].lower()
    return state
def check_vendor(state: ProcureState):
    state['vendor_approved'] = True
    return state
graph = StateGraph(ProcureState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', check_vendor)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()