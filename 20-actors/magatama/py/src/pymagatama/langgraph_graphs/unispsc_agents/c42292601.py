from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DilatorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_medical_standards(state: DilatorState):
    errors = []
    if not state['spec_data'].get('sterilization_method'):
        errors.append('Missing sterilization data')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(DilatorState)
graph.add_node('validate', validate_medical_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
