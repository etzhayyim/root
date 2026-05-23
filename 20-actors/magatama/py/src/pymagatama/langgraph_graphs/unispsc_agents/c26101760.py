from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChokeRodState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_specs(state: ChokeRodState):
    specs = state['spec_data']
    results = []
    if specs.get('tensile_strength', 0) < 500:
        results.append('Insufficient tensile strength')
    return {'validation_results': results, 'is_approved': len(results) == 0}

graph = StateGraph(ChokeRodState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
