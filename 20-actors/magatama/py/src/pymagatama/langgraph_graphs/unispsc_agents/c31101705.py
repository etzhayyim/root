from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: CastingState):
    errors = []
    if state['specs'].get('tensile_strength_mpa', 0) < 200:
        errors.append('Insufficient tensile strength')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_by_validation(state: CastingState):
    return 'process' if state['validation_passed'] else 'reject'

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: print('Fabrication approved'))
graph.add_node('reject', lambda s: print('Request rejected'))
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph.add_edge('reject', END)

app = graph.compile()