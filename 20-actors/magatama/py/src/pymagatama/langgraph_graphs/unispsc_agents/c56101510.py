from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PartitionState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: PartitionState):
    errors = []
    if 'fire_rating' not in state['spec_data']: errors.append('Missing fire rating')
    if 'installation_drawings' not in state['spec_data']: errors.append('Missing CAD blueprints')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: PartitionState):
    return 'process' if state['is_compliant'] else 'retry'

graph = StateGraph(PartitionState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()
