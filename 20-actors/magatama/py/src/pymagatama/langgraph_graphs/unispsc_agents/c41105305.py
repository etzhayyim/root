from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ElectrophoresisState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ElectrophoresisState):
    errors = []
    if 'voltage' not in state['specs']: errors.append('Missing voltage rating')
    return {'validation_errors': errors}

def check_compliance(state: ElectrophoresisState):
    is_valid = len(state['validation_errors']) == 0
    return {'approved': is_valid}

graph = StateGraph(ElectrophoresisState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()