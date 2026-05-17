from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IronRodState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_dimensions(state: IronRodState):
    errors = []
    if state['specs'].get('diameter', 0) <= 0:
        errors.append('Invalid Diameter')
    return {'validation_errors': errors}

def check_certification(state: IronRodState):
    approved = 'Mill Test Certificate' in state['specs'].get('docs', [])
    return {'approved': approved}

graph = StateGraph(IronRodState)
graph.add_node('validate', validate_dimensions)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()