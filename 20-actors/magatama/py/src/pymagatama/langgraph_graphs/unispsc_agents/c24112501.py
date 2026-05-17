from typing import TypedDict
from langgraph.graph import StateGraph, END

class CartonState(TypedDict):
    dimensions: dict
    board_quality: str
    validation_passed: bool

def validate_specs(state: CartonState):
    # Basic logic for checking if dimensions and board quality meet requirements
    is_valid = state['board_quality'] in ['Single-wall', 'Double-wall']
    return {'validation_passed': is_valid}

def process_order(state: CartonState):
    print('Processing shipment packaging constraints...')
    return state

graph = StateGraph(CartonState)
graph.add_node('validate', validate_specs)
graph.add_node('order', process_order)
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph.set_entry_point('validate')
graph = graph.compile()