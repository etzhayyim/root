from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrachytherapyState(TypedDict):
    seed_type: str
    activity_level: float
    compliance_cleared: bool

def validate_safety_protocols(state: BrachytherapyState):
    # Simulate validation of radiation safety and regulatory criteria
    state['compliance_cleared'] = state['activity_level'] > 0
    return state

def check_inventory_status(state: BrachytherapyState):
    print('Checking radioactive material compliance...')
    return state

graph = StateGraph(BrachytherapyState)
graph.add_node('validate', validate_safety_protocols)
graph.add_node('check', check_inventory_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()
