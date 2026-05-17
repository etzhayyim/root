from typing import TypedDict
from langgraph.graph import StateGraph, END

class ClothingState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_heat_specs(state: ClothingState):
    specs = state['spec_data']
    results = []
    if specs.get('iso_rating') not in ['A1', 'A2', 'B1']:
        results.append('ISO 11612 compliance invalid')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

graph = StateGraph(ClothingState)
graph.add_node('validation', validate_heat_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()