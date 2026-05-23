from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TransferFoilState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_foil_specs(state: TransferFoilState):
    errors = []
    if state['spec_data'].get('temp', 0) < 80:
        errors.append('Temperature requirement too low for industrial grade')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_by_validation(state: TransferFoilState):
    return 'approved' if state['approved'] else END

graph = StateGraph(TransferFoilState)
graph.add_node('validate', validate_foil_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
