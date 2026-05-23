from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MicrofilmState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_spec(state: MicrofilmState):
    errors = []
    if state['spec_data'].get('archival_life') < 100:
        errors.append('Insufficient archival life for microfilm standard.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(MicrofilmState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
