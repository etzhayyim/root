from typing import TypedDict
from langgraph.graph import StateGraph, END

class PoleState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: PoleState):
    required = ['Material Grade', 'Outer Diameter (mm)', 'Wall Thickness (mm)']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing mandatory specs']}

def structural_analysis(state: PoleState):
    if state.get('validation_passed'):
        print('Performing structural load analysis...')
    return state

graph = StateGraph(PoleState)
graph.add_node('validate', validate_specs)
graph.add_node('analysis', structural_analysis)
graph.add_edge('validate', 'analysis')
graph.add_edge('analysis', END)
graph.set_entry_point('validate')
graph = graph.compile()
