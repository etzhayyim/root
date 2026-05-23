from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    part_specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: ExtrusionState):
    errors = []
    if 'tolerance' not in state['part_specs']: errors.append('Missing tolerance spec')
    return {'validation_errors': errors}

def process_extrusion(state: ExtrusionState):
    is_valid = len(state['validation_errors']) == 0
    return {'is_approved': is_valid}

workflow = StateGraph(ExtrusionState)
workflow.add_node('validator', validate_dimensions)
workflow.add_node('processor', process_extrusion)
workflow.set_entry_point('validator')
workflow.add_edge('validator', 'processor')
workflow.add_edge('processor', END)
graph = workflow.compile()
