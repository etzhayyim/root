from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrickProcessingState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliance_score: float

def validate_specs(state: BrickProcessingState):
    specs = state['spec_data']
    is_valid = specs.get('acid_resistance', 0) > 98.0 and specs.get('porosity', 100) < 5
    return {'validation_result': is_valid, 'compliance_score': 1.0 if is_valid else 0.0}

graph = StateGraph(BrickProcessingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()