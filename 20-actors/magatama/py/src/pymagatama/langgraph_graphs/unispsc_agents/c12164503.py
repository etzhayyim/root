from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    material_id: str
    purity_level: float
    process_status: str

def validate_material(state: ProcessingState):
    is_valid = state['purity_level'] >= 99.99
    return {'process_status': 'validated' if is_valid else 'rejected'}

def perform_sintering(state: ProcessingState):
    return {'process_status': 'sintered'}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_material)
graph.add_node('sinter', perform_sintering)
graph.add_edge('validate', 'sinter')
graph.add_edge('sinter', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
