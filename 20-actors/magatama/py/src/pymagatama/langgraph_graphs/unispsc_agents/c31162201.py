from langgraph.graph import StateGraph, END
from typing import TypedDict

class RivetState(TypedDict):
    material: str
    grip_range: float
    tensile_strength: int
    is_compliant: bool

def validate_specs(state: RivetState):
    state['is_compliant'] = state['tensile_strength'] > 1000 and state['grip_range'] > 0
    return 'process_order' if state['is_compliant'] else 'reject_order'

def process_order(state: RivetState):
    print(f'Processing order for {state['material']} rivets.')
    return state

def reject_order(state: RivetState):
    print('Order rejected: Specifications below required safety threshold.')
    return state

graph = StateGraph(RivetState)
graph.add_node('validate', validate_specs)
graph.add_node('process_order', process_order)
graph.add_node('reject_order', reject_order)
graph.set_entry_point('validate')
graph.add_edge('process_order', END)
graph.add_edge('reject_order', END)
graph = graph.compile()