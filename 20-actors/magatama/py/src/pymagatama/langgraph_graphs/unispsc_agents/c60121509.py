from typing import TypedDict
from langgraph.graph import StateGraph, END

class CrayonState(TypedDict):
    product_specs: dict
    validation_passed: bool

def validate_non_toxicity(state: CrayonState):
    # Business logic for safety compliance
    compliant = state['product_specs'].get('non_toxic', False)
    return {'validation_passed': compliant}

def finalize_order(state: CrayonState):
    return {'validation_passed': True}

graph = StateGraph(CrayonState)
graph.add_node('safety_check', validate_non_toxicity)
graph.add_node('finalizer', finalize_order)
graph.add_edge('safety_check', 'finalizer')
graph.add_edge('finalizer', END)
graph.set_entry_point('safety_check')
graph = graph.compile()