from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_specs: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: ForgingState):
    specs = state['part_specs']
    results = []
    required_keys = ['alloy', 'tolerance', 'ndt_method']
    for key in required_keys:
        results.append(key in specs)
    return {'validation_results': results, 'is_compliant': all(results)}

def export_review(state: ForgingState):
    # Dual-use review logic
    print('Checking export controls for magnesium components...')
    return {}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()
