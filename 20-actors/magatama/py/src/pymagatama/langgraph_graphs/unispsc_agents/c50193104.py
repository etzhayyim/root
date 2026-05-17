from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SoupState(TypedDict):
    product_specs: dict
    compliance_checks: List[str]
    is_approved: bool

def validate_ingredients(state: SoupState):
    items = state['product_specs'].get('ingredients', [])
    valid = all(isinstance(i, str) for i in items)
    state['compliance_checks'].append('ingredients_checked')
    return {'is_approved': valid}

def check_shelf_life(state: SoupState):
    life = state['product_specs'].get('shelf_life', 0)
    state['compliance_checks'].append('shelf_life_verified')
    return {'is_approved': state['is_approved'] and (life > 0)}

graph = StateGraph(SoupState)
graph.add_node('validate', validate_ingredients)
graph.add_node('shelf_life', check_shelf_life)
graph.set_entry_point('validate')
graph.add_edge('validate', 'shelf_life')
graph.add_edge('shelf_life', END)
graph = graph.compile()