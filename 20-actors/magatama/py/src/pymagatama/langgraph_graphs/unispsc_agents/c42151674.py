from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DentalToolState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_autoclave_specs(state: DentalToolState):
    temp_rating = state['spec_data'].get('temp_rating', 0)
    if temp_rating < 134:
        state['validation_errors'].append('Insufficient heat resistance for medical sterilization.')
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(DentalToolState)
graph.add_node('validate', validate_autoclave_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()