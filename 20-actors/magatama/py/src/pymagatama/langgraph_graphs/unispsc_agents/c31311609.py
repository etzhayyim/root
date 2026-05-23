from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: PipeState):
    errors = []
    if state['spec_data'].get('pressure_rating', 0) < 1.0:
        errors.append('Insufficient pressure rating')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_workflow(state: PipeState):
    return {'validation_passed': True} if state['validation_passed'] else None

graph = StateGraph(PipeState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
