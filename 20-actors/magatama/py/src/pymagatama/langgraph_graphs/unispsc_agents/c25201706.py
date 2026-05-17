from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftState(TypedDict):
    part_number: str
    compliance_docs: list
    is_verified: bool

def validate_specs(state: AircraftState):
    # Simulate aerospace certification validation
    state['is_verified'] = all(d.startswith('DO-160') for d in state['compliance_docs'])
    print(f'Validation result for {state['part_number']}: {state['is_verified']}')
    return 'verified' if state['is_verified'] else 'failed'

graph = StateGraph(AircraftState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()