from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SteeringCableState(TypedDict):
    part_number: str
    spec_compliance: bool
    validation_log: List[str]

def validate_specs(state: SteeringCableState) -> SteeringCableState:
    state['validation_log'].append('Checking tensile strength and thermal tolerance...')
    state['spec_compliance'] = True
    return state

def route_procurement(state: SteeringCableState) -> str:
    return 'process_order' if state['spec_compliance'] else 'request_revision'

graph = StateGraph(SteeringCableState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()