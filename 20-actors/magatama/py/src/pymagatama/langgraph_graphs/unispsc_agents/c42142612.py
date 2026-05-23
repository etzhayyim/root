from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class IrrigationState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_syringe_spec(state: IrrigationState):
    errors = []
    if not state['spec_data'].get('sterilization_method'):
        errors.append('Missing sterilization certificate')
    if state['spec_data'].get('volume', 0) <= 0:
        errors.append('Invalid capacity volume')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(IrrigationState)
graph.add_node('validate', validate_syringe_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
