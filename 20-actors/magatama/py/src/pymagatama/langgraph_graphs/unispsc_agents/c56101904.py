from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnitureSpecState(TypedDict):
    part_type: str
    material: str
    load_limit: float
    verified: bool

def validate_specs(state: FurnitureSpecState):
    state['verified'] = state['load_limit'] > 0 and state['material'] in ['steel', 'aluminum', 'wood']
    return state

def inspect_quality(state: FurnitureSpecState):
    print(f'Inspecting {state["part_type"]} for structural integrity')
    return {'verified': True}

graph = StateGraph(FurnitureSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', inspect_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
