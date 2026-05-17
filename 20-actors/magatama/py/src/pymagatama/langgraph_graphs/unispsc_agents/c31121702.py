from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    material_spec: dict
    inspection_passed: bool
    is_compliant: bool

def validate_material(state: CastState):
    hardness = state['material_spec'].get('hardness', 0)
    return {'is_compliant': hardness > 200}

def inspect_casting(state: CastState):
    return {'inspection_passed': state['is_compliant']}

graph = StateGraph(CastState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', inspect_casting)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()