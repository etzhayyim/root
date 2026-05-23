from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    material: str
    food_grade: bool
    compliance_docs: List[str]

def validate_material(state: KitchenwareState):
    is_safe = state['material'] in ['Stainless Steel', 'Silicone', 'BPA-Free Plastic']
    return {'food_grade': is_safe}

def check_compliance(state: KitchenwareState):
    state['compliance_docs'].append('Food-Contact-Safety-Report')
    return state

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
