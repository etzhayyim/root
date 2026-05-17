from typing import TypedDict
from langgraph.graph import StateGraph, END

class PistonRodState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: PistonRodState):
    log = []
    required = ['Material Grade', 'Dimensional Tolerance']
    compliance = all(key in state['spec_data'] for key in required)
    log.append('Spec validation complete' if compliance else 'Missing critical fields')
    return {'validation_log': log, 'is_compliant': compliance}

graph = StateGraph(PistonRodState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()