from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlowCytometryState(TypedDict):
    reagent_info: dict
    validation_passed: bool

def validate_reagent_specs(state: FlowCytometryState):
    # Business logic for spec validation
    passed = all(key in state['reagent_info'] for key in ['clone', 'fluorophore'])
    return {'validation_passed': passed}

def check_temp_requirements(state: FlowCytometryState):
    # Logic for temperature sensitivity risk
    print('Verifying cold chain logistics')
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(FlowCytometryState)
graph.add_node('validate', validate_reagent_specs)
graph.add_node('logistics', check_temp_requirements)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()