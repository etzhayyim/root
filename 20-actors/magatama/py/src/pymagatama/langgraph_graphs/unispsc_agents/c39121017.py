from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PDUState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: PDUState):
    errors = []
    if not state['specifications'].get('voltage'):
        errors.append('Missing voltage rating')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: PDUState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(PDUState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

# Compile the graph
app = graph.compile()