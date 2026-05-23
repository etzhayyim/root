from typing import TypedDict
from langgraph.graph import StateGraph, END
class ProbeState(TypedDict):
    specs: dict
    validated: bool
    error: str
def validate_specs(state: ProbeState):
    required = ['range', 'interface']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'error': None if valid else 'Missing specs'}
def finalize_procurement(state: ProbeState):
    return {'validated': True}
graph = StateGraph(ProbeState)
graph.add_node('validator', validate_specs)
graph.add_node('finalizer', finalize_procurement)
graph.add_edge('validator', 'finalizer')
graph.add_edge('finalizer', END)
graph.set_entry_point('validator')
graph = graph.compile()
