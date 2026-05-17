from typing import TypedDict
from langgraph.graph import StateGraph, END

class BinderProcurementState(TypedDict):
    quantity: int
    material: str
    is_compliant: bool

def validate_spec(state: BinderProcurementState):
    state['is_compliant'] = state['material'] in ['polypropylene', 'recycled_paper']
    return 'validate_spec'

def process_order(state: BinderProcurementState):
    print(f'Processing order for {state['quantity']} binders')
    return 'process_order'

graph = StateGraph(BinderProcurementState)
graph.add_node('validate', validate_spec)
graph.add_node('order', process_order)
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph.set_entry_point('validate')
graph = graph.compile()