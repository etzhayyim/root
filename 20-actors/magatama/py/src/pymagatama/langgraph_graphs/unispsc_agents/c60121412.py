from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GlassSpecState(TypedDict):
    dimensions: dict
    quality_checks: List[str]
    approved: bool

def validate_dimensions(state: GlassSpecState):
    if state['dimensions'].get('thickness', 0) > 0:
        state['quality_checks'].append('DimensionsValid')
    return state

def verify_quality(state: GlassSpecState):
    if 'DimensionsValid' in state['quality_checks']:
        state['approved'] = True
    return state

graph = StateGraph(GlassSpecState)
graph.add_node('validate', validate_dimensions)
graph.add_node('verify', verify_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'verify')
graph.add_edge('verify', END)
graph = graph.compile()
