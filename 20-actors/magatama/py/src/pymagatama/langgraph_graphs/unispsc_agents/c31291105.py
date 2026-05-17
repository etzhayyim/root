from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: ExtrusionState):
    required = ['Material Grade', 'Pressure Rating MPa']
    missing = [f for f in required if f not in state['specs']]
    return {'validation_passed': len(missing) == 0, 'error_log': missing}

def structural_analysis(state: ExtrusionState):
    if state['validation_passed'] and state['specs'].get('Pressure Rating MPa', 0) > 50:
        return {'error_log': ['High pressure rating requires stress-strain analysis report']}
    return {}

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_specs)
graph.add_node('analysis', structural_analysis)
graph.add_edge('validate', 'analysis')
graph.add_edge('analysis', END)
graph.set_entry_point('validate')
graph = graph.compile()