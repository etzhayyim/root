from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class VegetableProcurementState(TypedDict):
    item_name: str
    inspection_passed: bool
    compliance_docs: List[str]

def validate_quality(state: VegetableProcurementState):
    # Simulate inspection logic for fresh produce
    state['inspection_passed'] = 'Pesticide Report' in state['compliance_docs']
    return state

def route_on_quality(state: VegetableProcurementState):
    return 'process_supply' if state['inspection_passed'] else 'reject_batch'

graph = StateGraph(VegetableProcurementState)
graph.add_node('inspection', validate_quality)
graph.add_node('process_supply', lambda x: x)
graph.add_node('reject_batch', lambda x: x)
graph.set_entry_point('inspection')
graph.add_conditional_edges('inspection', route_on_quality)
graph.add_edge('process_supply', END)
graph.add_edge('reject_batch', END)
graph = graph.compile()