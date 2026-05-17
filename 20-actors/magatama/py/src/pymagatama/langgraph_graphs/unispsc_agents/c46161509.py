from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SpeedStopperState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_durability(state: SpeedStopperState):
    errors = []
    if 'durability_rating' not in state['spec_data']:
        errors.append('Missing durability rating')
    return {'validation_errors': errors}

def approve_procurement(state: SpeedStopperState):
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(SpeedStopperState)
graph.add_node('validate', validate_durability)
graph.add_node('decision', approve_procurement)
graph.add_edge('validate', 'decision')
graph.add_edge('decision', END)
graph.set_entry_point('validate')