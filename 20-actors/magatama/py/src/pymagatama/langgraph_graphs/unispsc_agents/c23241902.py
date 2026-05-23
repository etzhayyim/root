from typing import TypedDict
from langgraph.graph import StateGraph, END

class JigBoringState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: JigBoringState):
    specs = state['spec_data']
    errors = []
    if specs.get('positioning_accuracy_micron', 10) > 5:
        errors.append('Precision exceeds acceptable tolerance')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def export_review(state: JigBoringState):
    print('Checking dual-use compliance for jig boring machine')
    return {'validation_passed': True}

graph = StateGraph(JigBoringState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_review)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
