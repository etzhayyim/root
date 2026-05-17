from typing import TypedDict
from langgraph.graph import StateGraph, END

class QuiltState(TypedDict):
    spec: dict
    is_compliant: bool

def validate_quilting_spec(state: QuiltState):
    required = ['material_composition', 'flame_retardancy_certification']
    compliance = all(k in state['spec'] for k in required)
    return {'is_compliant': compliance}

graph = StateGraph(QuiltState)
graph.add_node('validate', validate_quilting_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()