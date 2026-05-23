from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SoftballGloveState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: SoftballGloveState):
    errors = []
    if state['specs'].get('size', 0) < 8 or state['specs'].get('size', 0) > 15:
        errors.append('Size out of professional league range.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: SoftballGloveState):
    return 'valid' if state['is_compliant'] else 'invalid'

graph = StateGraph(SoftballGloveState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
