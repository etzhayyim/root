from typing import TypedDict
from langgraph.graph import StateGraph, END

class AnalyzerState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_chemistry_specs(state: AnalyzerState):
    # Business logic for checking analyzer chemical compatibility
    req = state['spec_data']
    errors = []
    if 'material' not in req: errors.append('Missing material info')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: AnalyzerState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(AnalyzerState)
graph.add_node('validate', validate_chemistry_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
