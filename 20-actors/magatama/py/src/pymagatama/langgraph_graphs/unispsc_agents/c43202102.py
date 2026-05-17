from typing import TypedDict
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    item_name: str
    material_check: str
    is_compliant: bool

def validate_material(state: StorageState):
    # Simplified logic to check if material meets standard storage safety requirements
    compliant = 'anti-static' in state['material_check'].lower()
    return {'is_compliant': compliant}

graph = StateGraph(StorageState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()