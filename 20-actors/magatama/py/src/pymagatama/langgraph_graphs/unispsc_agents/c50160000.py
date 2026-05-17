from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodProcurementState(TypedDict):
    product_name: str
    expiry_check_passed: bool
    compliance_validated: bool

def validate_food_standards(state: FoodProcurementState):
    print(f'Validating standards for {state['product_name']}')
    return {'compliance_validated': True}

def check_expiry(state: FoodProcurementState):
    print('Checking shelf life constraints...')
    return {'expiry_check_passed': True}

graph = StateGraph(FoodProcurementState)
graph.add_node('validate_standards', validate_food_standards)
graph.add_node('check_expiry', check_expiry)
graph.set_entry_point('validate_standards')
graph.add_edge('validate_standards', 'check_expiry')
graph.add_edge('check_expiry', END)
graph = graph.compile()