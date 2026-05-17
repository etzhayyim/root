from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    specs: dict
    approved: bool
    error: str

def validate_specs(state: ForgingState):
    required = ['alloy', 'dimensions', 'hardness']
    if all(k in state['specs'] for k in required):
        return {'approved': True}
    return {'approved': False, 'error': 'Missing core specifications'}

def conduct_inspection(state: ForgingState):
    print('Performing dimensional CAD analysis...')
    return {'approved': True}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', conduct_inspection)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()