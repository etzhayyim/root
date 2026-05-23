from typing import TypedDict
from langgraph.graph import StateGraph, END

class RehabEquipmentState(TypedDict):
    item_name: str
    weight_kg: float
    safety_check_passed: bool

def validate_spec(state: RehabEquipmentState):
    state['safety_check_passed'] = state['weight_kg'] > 0
    return state

def check_durability(state: RehabEquipmentState):
    print(f'Checking seams for {state['item_name']}')
    return {'safety_check_passed': state['safety_check_passed']}

graph = StateGraph(RehabEquipmentState)
graph.add_node('validate', validate_spec)
graph.add_node('durability', check_durability)
graph.add_edge('validate', 'durability')
graph.add_edge('durability', END)
graph.set_entry_point('validate')
graph = graph.compile()
