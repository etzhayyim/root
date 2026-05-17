from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlternatorState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_log: list

def validate_specs(state: AlternatorState):
    required = ['VoltageOutput', 'AmperageRating']
    status = all(k in state['spec_data'] for k in required)
    return {'validation_status': status, 'error_log': [] if status else ['Missing mandatory specs']}

def approval_step(state: AlternatorState):
    return {'validation_status': True}

graph = StateGraph(AlternatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()