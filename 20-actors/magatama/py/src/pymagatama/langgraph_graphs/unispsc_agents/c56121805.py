from typing import TypedDict
from langgraph.graph import StateGraph, END

class FileSpecs(TypedDict):
    material: str
    size: str
    capacity: int

def validate_specs(state: FileSpecs):
    if state['capacity'] <= 0: raise ValueError('Invalid capacity')
    return {'status': 'validated'}

graph = StateGraph(FileSpecs)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()