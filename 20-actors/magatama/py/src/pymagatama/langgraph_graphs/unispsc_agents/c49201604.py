from langgraph.graph import StateGraph, END
from typing import TypedDict

class FitnessEquipmentState(TypedDict):
    item_name: str
    capacity: float
    safety_check_passed: bool

def validate_specs(state: FitnessEquipmentState):
    state['safety_check_passed'] = state['capacity'] > 0
    return state

graph = StateGraph(FitnessEquipmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
