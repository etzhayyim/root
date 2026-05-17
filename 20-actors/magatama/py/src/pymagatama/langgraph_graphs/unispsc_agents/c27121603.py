from typing import TypedDict
from langgraph.graph import StateGraph, END

class PistonRodState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: list[str]

def validate_specs(state: PistonRodState):
    required = ['Material Grade', 'Surface Hardness (HRC)', 'Chrome Plating Thickness']
    passed = all(key in state['spec_data'] for key in required)
    return {'validation_passed': passed, 'log': ['Validation checked']}

def approval_step(state: PistonRodState):
    return {'log': ['Sent to engineering for quality review']}

graph = StateGraph(PistonRodState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()