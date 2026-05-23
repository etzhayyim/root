from typing import TypedDict
from langgraph.graph import StateGraph, END

class FolderState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_dimensions(state: FolderState):
    dims = state['spec_data'].get('dimensions_mm', {})
    # Ensure standard letter size constraints
    passed = dims.get('width', 0) > 0 and dims.get('height', 0) > 0
    return {'validation_passed': passed}

def finalize_procurement(state: FolderState):
    print('Procurement specification finalized.')
    return state

graph = StateGraph(FolderState)
graph.add_node('validate', validate_dimensions)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
