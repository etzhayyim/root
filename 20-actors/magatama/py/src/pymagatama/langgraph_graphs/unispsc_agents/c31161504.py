from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MachineScrewState(TypedDict):
    spec_requirements: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: MachineScrewState):
    results = []
    if 'material' not in state['spec_requirements']: results.append('Missing material grade')
    if 'tensile_strength' not in state['spec_requirements']: results.append('Missing strength rating')
    return {'validation_results': results, 'approved': len(results) == 0}

def finalize_order(state: MachineScrewState):
    return {'approved': state.get('approved', False)}

graph = StateGraph(MachineScrewState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
process = graph.compile()