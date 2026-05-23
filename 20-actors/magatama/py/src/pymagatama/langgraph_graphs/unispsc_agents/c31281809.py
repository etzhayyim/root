from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PunchComponentState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: PunchComponentState):
    errors = []
    if 'tolerance' not in state['spec_data']:
        errors.append('Missing required dimensional tolerance.')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(PunchComponentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
