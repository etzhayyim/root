from typing import TypedDict
from langgraph.graph import StateGraph, END

class MachineState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: MachineState):
    errors = []
    if state['spec_data'].get('press_tonnage_capacity', 0) <= 0:
        errors.append('Invalid tonnage capacity')
    return {'validation_results': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: MachineState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(MachineState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
