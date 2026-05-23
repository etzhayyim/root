from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class StationeryState(TypedDict):
    item_code: str
    spec_data: dict
    validation_passed: bool
    approval_workflow: List[str]

def validate_specs(state: StationeryState):
    # Basic validation logic for sticky notes
    passed = 'adhesive_strength' in state['spec_data'] and 'size_dimensions' in state['spec_data']
    return {'validation_passed': passed}

def route_procurement(state: StationeryState):
    return 'process_approval' if state['validation_passed'] else END

def process_approval(state: StationeryState):
    return {'approval_workflow': ['quality_check', 'procurement_authorized']}

graph = StateGraph(StationeryState)
graph.add_node('validate', validate_specs)
graph.add_node('process_approval', process_approval)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement)
graph.add_edge('process_approval', END)
graph = graph.compile()
