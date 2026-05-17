from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShoeInsoleState(TypedDict):
    specs: dict
    approved: bool

def validate_material(state: ShoeInsoleState):
    print('Validating material safety standards...')
    state['approved'] = 'antibacterial' in state['specs']
    return state

def finalize_order(state: ShoeInsoleState):
    print('Order processed.' if state['approved'] else 'Order rejected.')
    return state

graph = StateGraph(ShoeInsoleState)
graph.add_node('validate', validate_material)
graph.add_node('finish', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)