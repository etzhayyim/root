from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GumState(TypedDict):
    product_name: str
    ingredients: List[str]
    safety_verified: bool
    approved: bool

def validate_ingredients(state: GumState):
    # Business logic for gum ingredient compliance check
    forbidden = ['unregulated_additives', 'banned_dyes']
    valid = not any(item in forbidden for item in state['ingredients'])
    return {**state, 'safety_verified': valid}

def approval_step(state: GumState):
    return {**state, 'approved': state['safety_verified']}

graph = StateGraph(GumState)
graph.add_node('validate', validate_ingredients)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
