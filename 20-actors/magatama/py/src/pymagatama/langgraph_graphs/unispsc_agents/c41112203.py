from typing import TypedDict
from langgraph.graph import StateGraph, END

class MeltingPointState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_log: list

def validate_specs(state: MeltingPointState):
    required = ['measurement_range_celsius', 'accuracy_tolerance']
    valid = all(key in state['spec_data'] for key in required)
    return {'validation_status': valid, 'error_log': [] if valid else ['Missing specs']}

def approval_step(state: MeltingPointState):
    return {'validation_status': True}

graph = StateGraph(MeltingPointState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()