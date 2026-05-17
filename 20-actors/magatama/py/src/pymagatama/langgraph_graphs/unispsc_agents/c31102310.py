from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastingState(TypedDict):
    part_id: str
    specs: dict
    validated: bool
    errors: List[str]

def validate_casting_specs(state: CastingState):
    errors = []
    if 'tolerance' not in state['specs']: errors.append('Missing tolerance criteria')
    if 'material_grade' not in state['specs']: errors.append('Missing material grade')
    return {'validated': len(errors) == 0, 'errors': errors}

def route_by_validation(state: CastingState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(CastingState)
graph.add_node('validate', validate_casting_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()