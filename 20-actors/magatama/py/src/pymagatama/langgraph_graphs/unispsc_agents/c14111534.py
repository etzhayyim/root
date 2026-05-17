from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class FilingState(TypedDict):
    document_metadata: dict
    storage_requirements: list[str]
    validation_log: Annotated[list[str], operator.add]

def validate_materials(state: FilingState) -> FilingState:
    material = state['document_metadata'].get('material', 'unknown')
    status = 'Pass' if material in ['plastic', 'recycled_paper'] else 'Fail'
    return {'validation_log': [f'Material validation: {status} for {material}']}

def check_capacity(state: FilingState) -> FilingState:
    capacity = state['document_metadata'].get('capacity_sheets', 0)
    if capacity > 500:
        return {'validation_log': ['Capacity Warning: Exceeds standard binder limit']}
    return {'validation_log': ['Capacity: Within standard range']}

def build_graph():
    graph = StateGraph(FilingState)
    graph.add_node('validate_materials', validate_materials)
    graph.add_node('check_capacity', check_capacity)
    graph.set_entry_point('validate_materials')
    graph.add_edge('validate_materials', 'check_capacity')
    graph.add_edge('check_capacity', END)
    return graph.compile()

graph = build_graph()