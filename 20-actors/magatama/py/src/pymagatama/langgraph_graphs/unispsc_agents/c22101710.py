from typing import TypedDict
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_fastener_specs(state: FastenerState):
    required = ['material_grade', 'tensile_strength']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def route_by_validation(state: FastenerState):
    return 'process' if state['validated'] else 'end'

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_fastener_specs)
graph.add_edge('validate', 'end')
graph.set_entry_point('validate')
graph.set_finish_point('end')
graph = graph.compile()