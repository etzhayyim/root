from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ServoState):
    errors = []
    if 'voltage' not in state['specs']:
        errors.append('Missing input voltage rating')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()