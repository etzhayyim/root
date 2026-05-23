from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ServoState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ServoState):
    errors = []
    if not state['spec_data'].get('torque_rating_nm'):
        errors.append('Missing torque rating')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
