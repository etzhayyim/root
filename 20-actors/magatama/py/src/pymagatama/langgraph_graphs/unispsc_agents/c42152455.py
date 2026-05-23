from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    product_spec: dict
    validation_status: str

def validate_materials(state: DentalState):
    material = state['product_spec'].get('material', '')
    status = 'PASS' if material in ['Stainless Steel', 'Polypropylene'] else 'FAIL'
    return {'validation_status': status}

def check_sterilization(state: DentalState):
    return {'validation_status': 'PASS' if state['product_spec'].get('autoclave_safe') else 'FAIL'}

graph = StateGraph(DentalState)
graph.add_node('MaterialCheck', validate_materials)
graph.add_node('SterileCheck', check_sterilization)
graph.set_entry_point('MaterialCheck')
graph.add_edge('MaterialCheck', 'SterileCheck')
graph.add_edge('SterileCheck', END)
graph = graph.compile()
