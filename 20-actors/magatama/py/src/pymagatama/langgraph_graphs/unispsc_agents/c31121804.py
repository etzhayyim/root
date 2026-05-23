from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_chemistry(state: CastingState):
    # Simulate material compliance check for stainless steel grades
    has_errors = False
    if 'material_grade' not in state['part_specs']:
        state['validation_errors'].append('Missing grade info')
        has_errors = True
    return {'is_compliant': not has_errors}

def check_geometry(state: CastingState):
    # Validate tolerance dimensions
    if 'tolerance' not in state['part_specs']:
        state['validation_errors'].append('Tolerances undefined')
    return state

graph = StateGraph(CastingState)
graph.add_node('chemistry', validate_chemistry)
graph.add_node('geometry', check_geometry)
graph.set_entry_point('chemistry')
graph.add_edge('chemistry', 'geometry')
graph.add_edge('geometry', END)
app = graph.compile()
