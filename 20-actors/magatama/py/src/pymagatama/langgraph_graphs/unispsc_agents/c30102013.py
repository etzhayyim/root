from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FoilState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_foil_specs(state: FoilState):
    errors = []
    if state['spec_data'].get('thickness_microns', 0) < 10:
        errors.append('Foil thickness below standard safety threshold')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(FoilState)
graph.add_node('validate', validate_foil_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
