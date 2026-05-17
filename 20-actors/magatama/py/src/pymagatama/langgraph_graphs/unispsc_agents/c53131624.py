from typing import TypedDict
from langgraph.graph import StateGraph, END

class WipeState(TypedDict):
    product_specs: dict
    compliance_ok: bool

def validate_ingredients(state: WipeState):
    ingredients = state['product_specs'].get('ingredients', [])
    restricted = ['parabens', 'formaldehyde']
    return {'compliance_ok': not any(i in restricted for i in ingredients)}

def finalize_check(state: WipeState):
    return 'passed' if state['compliance_ok'] else 'failed'

graph = StateGraph(WipeState)
graph.add_node('validate', validate_ingredients)
graph.add_node('final', finalize_check)
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph.set_entry_point('validate')
graph = graph.compile()