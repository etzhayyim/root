from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    weight_kg: float
    material: str
    safety_compliant: bool

def validate_specs(state: State):
    is_valid = state['weight_kg'] > 0 and state['material'] != 'unknown'
    return {'safety_compliant': is_valid}

def approval_node(state: State):
    print(f'Processing weight: {state['weight_kg']}kg')
    return {}

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
