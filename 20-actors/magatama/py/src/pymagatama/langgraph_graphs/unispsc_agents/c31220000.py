from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DyeTanningState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_chemical_specs(state: DyeTanningState):
    errors = []
    if 'cas_number' not in state['spec_data']:
        errors.append('Missing CAS number')
    if state['spec_data'].get('purity', 0) < 95:
        errors.append('Purity below industry threshold')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(DyeTanningState)
graph.add_node('validate', validate_chemical_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
