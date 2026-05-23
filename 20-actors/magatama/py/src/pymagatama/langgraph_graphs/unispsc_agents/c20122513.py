from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BoltState(TypedDict):
    bolt_id: str
    spec_compliance: bool
    inspection_results: List[str]
    approved: bool

def validate_material(state: BoltState):
    # Simulate material validation logic
    state['inspection_results'].append('Material grade verified')
    return {'spec_compliance': True}

def perform_quality_check(state: BoltState):
    # Simulate QC logic
    state['inspection_results'].append('Dimensional tolerance check passed')
    return {'approved': True}

graph = StateGraph(BoltState)
graph.add_node('validate_material', validate_material)
graph.add_node('perform_quality_check', perform_quality_check)
graph.add_edge('validate_material', 'perform_quality_check')
graph.add_edge('perform_quality_check', END)
graph.set_entry_point('validate_material')
graph = graph.compile()
