from typing import TypedDict
from langgraph.graph import StateGraph, END

class SprayEquipState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: SprayEquipState):
    required = ['tank_capacity_liters', 'chemical_resistance_rating']
    passed = all(k in state['specs'] for k in required)
    return {**state, 'validation_passed': passed}

def route_by_specs(state: SprayEquipState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(SprayEquipState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
