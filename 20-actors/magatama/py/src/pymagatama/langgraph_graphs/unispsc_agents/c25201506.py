from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftComponentState(TypedDict):
    part_number: str
    certification_docs: list
    inspection_passed: bool

def validate_specs(state: AircraftComponentState):
    # Simulate aerospace validation logic
    state['inspection_passed'] = len(state['certification_docs']) > 0
    return state

def export_control_check(state: AircraftComponentState):
    print(f'Checking export status for {state['part_number']}')
    return state

graph = StateGraph(AircraftComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
