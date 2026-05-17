from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict): n
    product_info: dict
    validation_passed: bool

def validate_pharma(state: DrugState):
    print('Validating pharmacological compliance...')
    state['validation_passed'] = 'batch_no' in state['product_info'] and 'temp_range' in state['product_info']
    return state

def check_expiry(state: DrugState):
    print('Checking expiry date requirements...')
    return state

graph = StateGraph(DrugState)
graph.add_node('validate', validate_pharma)
graph.add_node('expiry_check', check_expiry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry_check')
graph.add_edge('expiry_check', END)
graph = graph.compile()