from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: TractorState):
    required = ['hp', 'emission_standard']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: TractorState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(TractorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: print('Processing tractor order...'))
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
