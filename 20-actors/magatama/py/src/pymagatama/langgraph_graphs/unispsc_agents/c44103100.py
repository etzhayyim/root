from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SupplyState(TypedDict):
    part_number: str
    compatibility_verified: bool
    yield_specs: dict
    approved: bool

def check_compatibility(state: SupplyState):
    print(f'Verifying compatibility for {state['part_number']}')
    return {'compatibility_verified': True}

def validate_specs(state: SupplyState):
    print('Validating yield and environmental specs')
    return {'approved': state.get('compatibility_verified', False)}

graph = StateGraph(SupplyState)
graph.add_node('check_compatibility', check_compatibility)
graph.add_node('validate_specs', validate_specs)
graph.set_entry_point('check_compatibility')
graph.add_edge('check_compatibility', 'validate_specs')
graph.add_edge('validate_specs', END)
graph = graph.compile()