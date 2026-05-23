from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeSpecState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    is_compliant: bool

def validate_dimensions(state: PipeSpecState):
    nps = state['spec_data'].get('nps')
    wall_thickness = state['spec_data'].get('wall_thickness')
    results = state.get('validation_results', [])
    if nps and wall_thickness:
        results.append('Dimension check passed')
    return {'validation_results': results}

def compliant_check(state: PipeSpecState):
    is_compliant = len(state['validation_results']) > 0
    return {'is_compliant': is_compliant}

graph = StateGraph(PipeSpecState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', compliant_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
