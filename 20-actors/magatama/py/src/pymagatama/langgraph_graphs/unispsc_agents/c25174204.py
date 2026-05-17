from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteeringState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: SteeringState):
    fields = ['ISO 26262', 'Voltage']
    valid = all(f in state['spec_data'] for f in fields)
    return {'validated': valid, 'error_log': [] if valid else ['Missing specs']}

def final_check(state: SteeringState):
    return {**state}

graph = StateGraph(SteeringState)
graph.add_node('validate', validate_specs)
graph.add_node('final', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()