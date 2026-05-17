from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TagState(TypedDict):
    material_type: str
    pull_strength: float
    is_compliant: bool

def validate_materials(state: TagState):
    return {'is_compliant': state['material_type'] in ['Nylon', 'Polypropylene']}

def check_durability(state: TagState):
    return {'is_compliant': state.get('is_compliant', False) and state['pull_strength'] > 5.0}

graph = StateGraph(TagState)
graph.add_node('validate', validate_materials)
graph.add_node('durability', check_durability)
graph.set_entry_point('validate')
graph.add_edge('validate', 'durability')
graph.add_edge('durability', END)
graph = graph.compile()