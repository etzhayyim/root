from typing import TypedDict
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    spec: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: IncubatorState):
    required = ['gas_control', 'humidity_range', 'chamber_volume']
    compliance = all(k in state['spec'] for k in required)
    return {'validation_results': ['Specs checked'], 'is_compliant': compliance}

def approval_step(state: IncubatorState):
    return {'validation_results': state['validation_results'] + ['Technical review passed']}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
