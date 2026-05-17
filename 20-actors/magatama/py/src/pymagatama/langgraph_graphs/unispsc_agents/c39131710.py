from typing import TypedDict
from langgraph.graph import StateGraph, END

class WirewayState(TypedDict):
    specs: dict
    validation_results: list
    is_approved: bool

def validate_specs(state: WirewayState):
    required = ['Material Type', 'Dimensions']
    results = [s for s in required if s in state['specs']]
    return {'validation_results': results, 'is_approved': len(results) == len(required)}

graph = StateGraph(WirewayState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()