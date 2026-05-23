from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OphthalmicState(TypedDict):
    part_id: str
    specifications: dict
    validation_results: List[str]

def validate_biocompatibility(state: OphthalmicState):
    if 'iso_10993' not in state['specifications'].get('certifications', []):
        return {'validation_results': ['Biocompatibility certification missing']}
    return {'validation_results': ['Biocompatibility verified']}

def check_dimensions(state: OphthalmicState):
    if 'dimensions' not in state['specifications']:
        return {'validation_results': state['validation_results'] + ['Missing dimensions']}
    return {'validation_results': state['validation_results'] + ['Dimensions validated']}

graph = StateGraph(OphthalmicState)
graph.add_node('validate_bio', validate_biocompatibility)
graph.add_node('check_dims', check_dimensions)
graph.set_entry_point('validate_bio')
graph.add_edge('validate_bio', 'check_dims')
graph.add_edge('check_dims', END)
graph = graph.compile()
