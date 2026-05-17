from typing import TypedDict
from langgraph.graph import StateGraph, END
class VehicleState(TypedDict):
    vehicle_id: str
    specs: dict
    is_compliant: bool
def validate_specs(state: VehicleState):
    state['is_compliant'] = 'emission_standard' in state['specs'] and 'payload' in state['specs']
    return state
def update_registry(state: VehicleState):
    print(f'Registering vehicle {state.get('vehicle_id')} in procurement system...')
    return {'is_compliant': True}
graph = StateGraph(VehicleState)
graph.add_node('validate', validate_specs)
graph.add_node('register', update_registry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'register')
graph.add_edge('register', END)
graph = graph.compile()