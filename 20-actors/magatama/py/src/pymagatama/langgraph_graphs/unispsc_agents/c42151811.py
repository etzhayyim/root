from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalProductState(TypedDict):
    product_name: str
    compliance_docs: List[str]
    approved: bool

def validate_medical_specs(state: DentalProductState):
    # Simulate validation logic for dental consumables
    has_iso = any('ISO' in doc for doc in state['compliance_docs'])
    return {'approved': has_iso}

def update_inventory(state: DentalProductState):
    return {'approved': True}

graph = StateGraph(DentalProductState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('update', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'update')
graph.add_edge('update', END)
graph = graph.compile()
