from typing import TypedDict
from langgraph.graph import StateGraph, END

class CycleState(TypedDict):
    vin: str
    spec_sheet: dict
    approved: bool

def validate_emissions(state: CycleState):
    # Simulate regulatory validation logic for motorized cycles
    state['approved'] = state['spec_sheet'].get('emission_standard') == 'Euro5'
    return state

def check_battery_safety(state: CycleState):
    # Simulate safety inspection for electric components
    if 'battery_capacity_wh' in state['spec_sheet']:
        state['approved'] = state['approved'] and state['spec_sheet']['battery_capacity_wh'] < 5000
    return state

graph = StateGraph(CycleState)
graph.add_node('validate_emissions', validate_emissions)
graph.add_node('check_battery_safety', check_battery_safety)
graph.add_edge('validate_emissions', 'check_battery_safety')
graph.add_edge('check_battery_safety', END)
graph.set_entry_point('validate_emissions')