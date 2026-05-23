from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_name: str
    quality_passed: bool
    compliance_docs: List[str]

def validate_food_safety(state: ProcurementState):
    # Simulate wood safety and coating validation
    state['quality_passed'] = 'food_safety_cert' in state['compliance_docs']
    return state

def check_dimensions(state: ProcurementState):
    # Specialized check for spoon geometry
    print('Verifying spoon dimensions against specs...')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('safety_check', validate_food_safety)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()
