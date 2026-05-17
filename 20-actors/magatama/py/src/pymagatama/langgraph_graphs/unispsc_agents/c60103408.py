from typing import TypedDict
from langgraph.graph import StateGraph, END

class GeographyProcurementState(TypedDict):
    book_request: dict
    validation_status: bool
    approved: bool

def validate_curriculum(state: GeographyProcurementState):
    print('Validating curriculum alignment for: ', state['book_request'].get('title'))
    return {'validation_status': True}

def approval_step(state: GeographyProcurementState):
    return {'approved': state['validation_status']}

graph = StateGraph(GeographyProcurementState)
graph.add_node('validate', validate_curriculum)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()