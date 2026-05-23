from typing import TypedDict
from langgraph.graph import StateGraph, END

class WineState(TypedDict):
    vintage: str
    alcohol_content: float
    inventory_check: bool

def validate_specs(state: WineState):
    if state['alcohol_content'] > 20.0:
        return {'inventory_check': False}
    return {'inventory_check': True}

def approve_procurement(state: WineState):
    return 'Approved'

graph = StateGraph(WineState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
