from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StapleState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_specs(state: StapleState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material spec')
    if 'gauge' not in state['specs']: errors.append('Missing gauge value')
    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}

def route_by_compliance(state: StapleState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(StapleState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', 'process')
graph.set_entry_point('validate')
graph.add_edge('process', END)
graph = graph.compile()