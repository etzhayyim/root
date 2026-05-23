from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class NewsProcurementState(TypedDict):
    subscription_items: List[str]
    delivery_locations: List[str]
    is_verified: bool
def validate_subscription(state: NewsProcurementState):
    state['is_verified'] = len(state['subscription_items']) > 0
    return state
def finalize_order(state: NewsProcurementState):
    return {'is_verified': True}
graph = StateGraph(NewsProcurementState)
graph.add_node('validate', validate_subscription)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
