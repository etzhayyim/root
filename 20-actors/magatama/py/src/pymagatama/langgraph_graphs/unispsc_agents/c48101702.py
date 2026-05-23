from typing import TypedDict
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    spec_data: dict
    validation_logger: list

def validate_food_safety(state: DispenserState):
    compliance = state['spec_data'].get('food_grade_certification', False)
    log = 'Passed' if compliance else 'Failed: Missing Food Grade Certification'
    return {'validation_logger': [log]}

def check_cooling(state: DispenserState):
    cap = state['spec_data'].get('cooling_capacity_liters_per_hour', 0)
    log = 'Cooling capacity validated' if cap > 0 else 'Error: Low capacity'
    return {'validation_logger': state['validation_logger'] + [log]}

builder = StateGraph(DispenserState)
builder.add_node('validate_safety', validate_food_safety)
builder.add_node('check_cooling', check_cooling)
builder.set_entry_point('validate_safety')
builder.add_edge('validate_safety', 'check_cooling')
builder.add_edge('check_cooling', END)
graph = builder.compile()
