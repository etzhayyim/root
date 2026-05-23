from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CommunicationBoardState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_accessibility_specs(state: CommunicationBoardState):
    errors = []
    if state['spec_data'].get('contrast_ratio', 0) < 4.5:
        errors.append('Contrast ratio below accessibility standards.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(CommunicationBoardState)
graph.add_node('validate', validate_accessibility_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
