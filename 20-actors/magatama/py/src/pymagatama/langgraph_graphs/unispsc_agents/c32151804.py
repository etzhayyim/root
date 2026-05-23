from typing import TypedDict
from langgraph.graph import StateGraph, END

class SafetyScannerState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_safety_specs(state: SafetyScannerState):
    specs = state['spec_data']
    results = []
    if specs.get('SIL') not in ['SIL2', 'SIL3']:
        results.append('Invalid Safety Integrity Level')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def check_compliance(state: SafetyScannerState):
    return 'pass' if state['is_compliant'] else 'fail'

graph = StateGraph(SafetyScannerState)
graph.add_node('validate', validate_safety_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
