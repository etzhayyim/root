from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_food_safety(state: KitchenwareState):
    checks = ['material_grade', 'food_contact_certification']
    passed = all(key in state['spec_data'] for key in checks)
    return {**state, 'validation_passed': passed}

def process_procurement(state: KitchenwareState):
    print('Processing commercial strainer procurement metadata.')
    return state

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_food_safety)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.compile()
