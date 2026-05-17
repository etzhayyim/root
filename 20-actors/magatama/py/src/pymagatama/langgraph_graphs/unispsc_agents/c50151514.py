from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FoodSafetyState(TypedDict):
    product_name: str
    compliance_docs: List[str]
    passed_inspection: bool

def validate_certification(state: FoodSafetyState):
    # Simulate audit for ISO 22000 or HACCP docs
    state['passed_inspection'] = 'ISO22000' in state['compliance_docs']
    return state

def check_expiry(state: FoodSafetyState):
    print('Checking shelf life for edible fats')
    return state

graph = StateGraph(FoodSafetyState)
graph.add_node('validate', validate_certification)
graph.add_node('expiry', check_expiry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
app = graph.compile()