from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenApplianceState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_food_safety(state: KitchenApplianceState):
    is_certified = state['spec_data'].get('food_grade_cert', False)
    return {'is_compliant': is_certified}

def check_electrical(state: KitchenApplianceState):
    wattage = state['spec_data'].get('wattage', 0)
    return {'is_compliant': state['is_compliant'] and (100 <= wattage <= 1500)}

graph = StateGraph(KitchenApplianceState)
graph.add_node('safety_check', validate_food_safety)
graph.add_node('elec_check', check_electrical)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'elec_check')
graph.add_edge('elec_check', END)
graph = graph.compile()
