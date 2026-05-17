from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ComponentState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: ComponentState):
    errors = []
    if 'alloy' not in state['spec_data']: errors.append('Missing alloy type')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def process_components(state: ComponentState):
    return {'status': 'processed'}

graph = StateGraph(ComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_components)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()