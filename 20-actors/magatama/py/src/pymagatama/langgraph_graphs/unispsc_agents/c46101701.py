from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AmmSpecState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    is_approved: bool

def validate_tech_specs(state: AmmSpecState):
    specs = state['spec_data']
    results = []
    if specs.get('mtbf', 0) < 5000:
        results.append('MTBF insufficient for battlefield requirements.')
    return {'validation_results': results, 'is_approved': len(results) == 0}

def security_clearance(state: AmmSpecState):
    # Simulate rigid export control check
    return {'validation_results': state['validation_results'] + ['Export control check passed']}

graph = StateGraph(AmmSpecState)
graph.add_node('validate_specs', validate_tech_specs)
graph.add_node('export_review', security_clearance)
graph.add_edge('validate_specs', 'export_review')
graph.add_edge('export_review', END)
graph.set_entry_point('validate_specs')
graph = graph.compile()
