from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TyingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: TyingState):
    errors = []
    if not state['spec_data'].get('safety_cert'):
        errors.append('Missing safety certification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def process_procurement(state: TyingState):
    print('Initiating procurement workflow for bundling machinery...')
    return {'approved': True}

graph = StateGraph(TyingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
