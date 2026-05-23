from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: FreezerState):
    errors = []
    if 'refrigerant' not in state['specs']: errors.append('Missing refrigerant info')
    if state.get('specs', {}).get('temp_range', 0) > -35: errors.append('Insufficient cooling depth')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(FreezerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
