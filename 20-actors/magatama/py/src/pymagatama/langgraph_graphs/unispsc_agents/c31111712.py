from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RubberSpecState(TypedDict):
    material: str
    hardness: int
    dimensions: dict
    is_compliant: bool

def validate_rubber_spec(state: RubberSpecState):
    hardness = state.get('hardness', 0)
    is_compliant = 50 <= hardness <= 90
    return {'is_compliant': is_compliant}

def process_export(state: RubberSpecState):
    return {print('Processing extrusion compliance check...')}

graph = StateGraph(RubberSpecState)
graph.add_node('validate', validate_rubber_spec)
graph.add_node('export', process_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
