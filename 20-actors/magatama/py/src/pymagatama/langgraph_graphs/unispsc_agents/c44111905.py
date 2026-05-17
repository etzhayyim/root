from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BoardState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_dimensions(state: BoardState):
    errs = []
    if not state['spec_data'].get('board_dimensions'): errs.append('Missing dimensions')
    return {'validation_errors': errs}

def check_material(state: BoardState):
    errs = state.get('validation_errors', [])
    if 'surface_material' not in state['spec_data']: errs.append('Material unspecified')
    return {'validation_errors': errs, 'approved': len(errs) == 0}

graph = StateGraph(BoardState)
graph.add_node('validate_dim', validate_dimensions)
graph.add_node('check_mat', check_material)
graph.set_entry_point('validate_dim')
graph.add_edge('validate_dim', 'check_mat')
graph.add_edge('check_mat', END)
graph = graph.compile()