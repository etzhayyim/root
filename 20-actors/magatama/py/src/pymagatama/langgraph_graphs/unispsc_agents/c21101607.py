from typing import TypedDict
from langgraph.graph import StateGraph, END

class MiningMachineryState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: MiningMachineryState):
    errors = []
    if state['spec_data'].get('operating_pressure', 0) > 5000:
        errors.append('Pressure exceeding regulatory safety limit')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: MiningMachineryState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(MiningMachineryState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
