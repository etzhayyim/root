from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveComponentState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: ValveComponentState):
    required = ['Material Grade', 'Outer Diameter Tolerance', 'Wall Thickness']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def structural_analysis(state: ValveComponentState):
    # Simulate CAD/FEA simulation integration
    return {'validation_passed': True}

graph = StateGraph(ValveComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('analysis', structural_analysis)
graph.add_edge('validate', 'analysis')
graph.add_edge('analysis', END)
graph.set_entry_point('validate')
graph = graph.compile()
