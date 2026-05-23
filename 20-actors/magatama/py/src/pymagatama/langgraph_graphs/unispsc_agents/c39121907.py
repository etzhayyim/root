from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ReceptacleState(TypedDict):
    part_number: str
    spec_compliance: bool
    safety_check: bool

def validate_specs(state: ReceptacleState):
    # Simulate electrical safety spec validation logic
    state['spec_compliance'] = len(state['part_number']) > 5
    return state

def run_safety_filter(state: ReceptacleState):
    # Simulate fire safety rating check
    state['safety_check'] = True
    return state

graph = StateGraph(ReceptacleState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', run_safety_filter)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
