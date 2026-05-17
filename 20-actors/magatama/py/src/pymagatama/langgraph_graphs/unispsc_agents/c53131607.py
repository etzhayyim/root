from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    product_name: str
    ingredients: List[str]
    compliance_docs: List[str]
    approved: bool

def validate_ingredients(state: ProcurementState):
    # Simulate safety check for cosmetic ingredients
    unsafe = {'parabens', 'formaldehyde'} 
    state['approved'] = not any(i.lower() in unsafe for i in state['ingredients'])
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_ingredients)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()