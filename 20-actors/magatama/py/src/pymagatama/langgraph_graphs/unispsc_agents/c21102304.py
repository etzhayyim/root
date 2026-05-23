from typing import TypedDict
from langgraph.graph import StateGraph, END

class HarvestSpecState(TypedDict):
    equipment_id: str
    specs: dict
    validation_passed: bool

def validate_specs(state: HarvestSpecState):
    required = ['engine_displacement_cc', 'harvesting_capacity_tons_hr']
    passed = all(k in state['specs'] for k in required)
    return {**state, 'validation_passed': passed}

def route_by_validation(state: HarvestSpecState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(HarvestSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
