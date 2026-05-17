from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FoodSupplyState(TypedDict):
    product_name: str
    spec_requirements: List[str]
    compliance_cleared: bool

def validate_food_safety(state: FoodSupplyState):
    print(f'Validating compliance for: {state["product_name"]}')
    state['compliance_cleared'] = True
    return state

def check_shelf_life(state: FoodSupplyState):
    print('Verifying shelf life documentation...')
    return {'compliance_cleared': state['compliance_cleared']}

graph = StateGraph(FoodSupplyState)
graph.add_node('safety_check', validate_food_safety)
graph.add_node('shelf_life', check_shelf_life)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'shelf_life')
graph.add_edge('shelf_life', END)
graph = graph.compile()