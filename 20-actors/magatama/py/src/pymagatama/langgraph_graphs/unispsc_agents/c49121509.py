from typing import TypedDict
from langgraph.graph import StateGraph, END

class StoveState(TypedDict):
    fuel_type: str
    safety_check_passed: bool
    validation_log: list

def validate_fuel(state: StoveState):
    valid = state['fuel_type'] in ['isobutane', 'propane', 'white_gas']
    return {'safety_check_passed': valid, 'validation_log': ['Fuel verified' if valid else 'Fuel invalid']}

def finalize_procurement(state: StoveState):
    return {'validation_log': state['validation_log'] + ['Procurement approved']}

graph = StateGraph(StoveState)
graph.add_node('fuel_check', validate_fuel)
graph.add_node('finalizer', finalize_procurement)
graph.add_edge('fuel_check', 'finalizer')
graph.add_edge('finalizer', END)
graph.set_entry_point('fuel_check')
graph = graph.compile()