from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_number: str
    specs: dict
    approved: bool

def validate_bearing_specs(state: BearingState):
    # Simulate CAD and load validation logic
    required_keys = ['load_rating', 'material', 'tolerance']
    state['approved'] = all(k in state['specs'] for k in required_keys)
    return state

def check_compliance(state: BearingState):
    print(f'Checking compliance for {state['part_number']}')
    return {'approved': state['approved']}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_bearing_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
