from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    specs: dict
    approved: bool
    validation_log: list

def validate_emissions(state: TractorState):
    emission_tier = state['specs'].get('engine_emission_standard')
    is_valid = emission_tier in ['Tier4', 'StageV']
    return {'approved': is_valid, 'validation_log': [f'Emission check: {is_valid}']}

def check_towing_capacity(state: TractorState):
    capacity = state['specs'].get('towing_capacity_kg', 0)
    valid = capacity > 1000
    return {'approved': state['approved'] and valid, 'validation_log': state['validation_log'] + [f'Towing check: {valid}']}

graph = StateGraph(TractorState)
graph.add_node('validate_emissions', validate_emissions)
graph.add_node('check_towing_capacity', check_towing_capacity)
graph.set_entry_point('validate_emissions')
graph.add_edge('validate_emissions', 'check_towing_capacity')
graph.add_edge('check_towing_capacity', END)
graph = graph.compile()
