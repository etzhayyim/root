from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class KitchenwareState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool

def validate_food_grade(state: KitchenwareState):
    state['is_compliant'] = 'food_grade_cert' in state['specs']
    return state

def check_thermal_specs(state: KitchenwareState):
    if state['is_compliant']:
        state['is_compliant'] = 'material_grade' in state['specs']
    return state

graph = StateGraph(KitchenwareState)
graph.add_node('validate_food_grade', validate_food_grade)
graph.add_node('check_thermal_specs', check_thermal_specs)
graph.add_edge('validate_food_grade', 'check_thermal_specs')
graph.add_edge('check_thermal_specs', END)
graph.set_entry_point('validate_food_grade')
graph = graph.compile()