from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FloorPanelState(TypedDict):
    dimensions: dict
    material: str
    compliance_docs: List[str]
    is_approved: bool

def validate_specs(state: FloorPanelState):
    # Business logic for panel verification
    compliant = state['dimensions'] and state['material'] != 'none'
    return {'is_approved': compliant}

def structural_analysis(state: FloorPanelState):
    print('Running structural load simulation...')
    return {'is_approved': state.get('is_approved', False)}

graph = StateGraph(FloorPanelState)
graph.add_node('validate', validate_specs)
graph.add_node('analysis', structural_analysis)
graph.set_entry_point('validate')
graph.add_edge('validate', 'analysis')
graph.add_edge('analysis', END)
graph = graph.compile()
