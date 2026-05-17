from langgraph.graph import StateGraph, END
from typing import TypedDict
class ProcurementState(TypedDict):
    material: str
    dimensions: float
    is_compliant: bool
def validate_specs(state: ProcurementState):
    state['is_compliant'] = state['material'] in ['Steel', 'PVC', 'Aluminum'] and state['dimensions'] > 0
    return state
def route_by_compliance(state: ProcurementState):
    return 'process_order' if state['is_compliant'] else 'manual_review'
def process_order(state: ProcurementState):
    print('Proceeding to procurement workflow')
    return state
def manual_review(state: ProcurementState):
    print('Flagging for manual inspection')
    return state
graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('process_order', process_order)
graph.add_node('manual_review', manual_review)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process_order', END)
graph.add_edge('manual_review', END)
graph = graph.compile()