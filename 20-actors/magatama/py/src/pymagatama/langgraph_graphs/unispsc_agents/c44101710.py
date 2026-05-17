from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_electrical_specs(state: ProcessingState):
    errors = []
    if 'resistance_ohms' not in state['specs']:
        errors.append('Missing resistance specifications')
    return {'validation_errors': errors}

def check_compliance(state: ProcessingState):
    compliant = len(state['validation_errors']) == 0
    return {'is_compliant': compliant}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_electrical_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()