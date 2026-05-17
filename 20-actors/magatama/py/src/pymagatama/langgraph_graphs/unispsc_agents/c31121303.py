from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: CastingState):
    errors = []
    if 'grade' not in state['spec_sheet']: errors.append('Missing material grade')
    if 'tolerance' not in state['spec_sheet']: errors.append('Missing tolerance data')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_by_validation(state: CastingState):
    return 'process' if state['approved'] else END

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'approved': True})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()