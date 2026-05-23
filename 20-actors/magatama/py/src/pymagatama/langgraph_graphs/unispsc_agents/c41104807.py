from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtractionState(TypedDict):
    spec_file: str
    validation_errors: list
    is_compliant: bool

def validate_extractors(state: ExtractionState):
    errors = []
    if 'solvent_safety' not in state['spec_file']:
        errors.append('Missing solvent safety protocol')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(ExtractionState)
graph.add_node('validate', validate_extractors)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
