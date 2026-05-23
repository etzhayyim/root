from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    part_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_magnesium_geometry(state: MagnesiumState):
    errors = []
    if not state['part_specs'].get('thickness'):
        errors.append('Missing thickness spec')
    return {'validation_errors': errors}

def check_dual_use(state: MagnesiumState):
    # Mock check for dual-use export control
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(MagnesiumState)
graph.add_node('validate', validate_magnesium_geometry)
graph.add_node('export_review', check_dual_use)
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph.set_entry_point('validate')
graph = graph.compile()
