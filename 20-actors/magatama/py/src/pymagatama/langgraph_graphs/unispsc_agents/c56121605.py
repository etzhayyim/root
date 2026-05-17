from typing import TypedDict
from langgraph.graph import StateGraph, END

class PartitionState(TypedDict):
    spec_data: dict
    approved: bool

def validate_safety(state: PartitionState):
    # Validate fire resistance and stability specs
    state['approved'] = 'fire_rating' in state['spec_data']
    return 'safety_validated'

def check_dimensions(state: PartitionState):
    # Ensure low-rise height constraints
    if state['spec_data'].get('height', 0) > 150:
        state['approved'] = False
    return 'dimensions_validated'

graph = StateGraph(PartitionState)
graph.add_node('safety_check', validate_safety)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()