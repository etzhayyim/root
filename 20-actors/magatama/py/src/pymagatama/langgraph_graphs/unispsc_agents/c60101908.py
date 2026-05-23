from typing import TypedDict
from langgraph.graph import StateGraph, END

class ResourceState(TypedDict):
    content: str
    is_validated: bool
    compliance_score: float

def validate_resource(state: ResourceState):
    # Simulate pedagogical content validation logic
    valid = len(state['content']) > 0
    return {'is_validated': valid, 'compliance_score': 1.0 if valid else 0.0}

def finalize_order(state: ResourceState):
    return {'content': 'Validated: ' + state['content']}

graph = StateGraph(ResourceState)
graph.add_node('validate', validate_resource)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
