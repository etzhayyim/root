from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    material_type: str
    spec_requirements: List[str]
    validation_passed: bool

def validate_specs(state: PackagingState):
    # Simulate spec validation logic for paper packaging
    required = ['gsm', 'strength']
    passed = all(item in state['spec_requirements'] for item in required)
    return {'validation_passed': passed}

def route_by_validation(state: PackagingState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
