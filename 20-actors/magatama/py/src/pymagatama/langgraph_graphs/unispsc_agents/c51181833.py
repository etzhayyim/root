from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    purity_level: float
    inspection_passed: bool

def validate_api_purity(state: PharmState):
    if state['purity_level'] >= 99.5:
        return {'inspection_passed': True}
    return {'inspection_passed': False}

def update_inventory(state: PharmState):
    if state['inspection_passed']:
        print(f'Batch {state['batch_id']} cleared for storage.')
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_api_purity)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()