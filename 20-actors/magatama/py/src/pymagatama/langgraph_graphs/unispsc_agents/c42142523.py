from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NeedleState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_needle(state: NeedleState):
    errors = []
    if state['spec_data'].get('sterilization') != 'Gamma':
         errors.append('Invalid sterilization method')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(NeedleState)
graph.add_node('validate', validate_needle)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()