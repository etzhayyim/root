from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    part_id: str
    spec_compliance: bool
    inspection_report: str

def validate_dimensions(state: ExtrusionState):
    # Simulate CAD variance check
    state['spec_compliance'] = True
    return 'passed'

def finalize_quality(state: ExtrusionState):
    state['inspection_report'] = 'Certified compliance'
    return 'completed'

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_dimensions)
graph.add_node('finalize', finalize_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)

compiled_graph = graph.compile()