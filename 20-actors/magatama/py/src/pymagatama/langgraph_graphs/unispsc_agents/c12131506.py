from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalOxideState(TypedDict):
    commodity_code: str
    purity: float
    inspection_passed: bool
    compliance_tags: List[str]

def validate_purity(state: MetalOxideState):
    passed = state['purity'] >= 99.9
    return {'inspection_passed': passed}

def route_compliance(state: MetalOxideState):
    if not state['inspection_passed']:
        return 'flag_for_review'
    return 'process_order'

def flag_for_review(state: MetalOxideState):
    return {'compliance_tags': ['MANUAL_REVIEW_REQUIRED']}

def process_order(state: MetalOxideState):
    return {'compliance_tags': ['READY_FOR_LOGISTICS']}

graph = StateGraph(MetalOxideState)
graph.add_node('validate', validate_purity)
graph.add_node('flag_for_review', flag_for_review)
graph.add_node('process_order', process_order)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_compliance)
graph.add_edge('flag_for_review', END)
graph.add_edge('process_order', END)
graph = graph.compile()