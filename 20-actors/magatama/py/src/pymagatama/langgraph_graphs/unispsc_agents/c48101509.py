from typing import TypedDict
from langgraph.graph import StateGraph, END

class FryerState(TypedDict):
    capacity: int
    safety_standard: str
    validation_passed: bool

def validate_specs(state: FryerState):
    passed = state['capacity'] > 0 and state['safety_standard'] == 'NSF'
    return {'validation_passed': passed}

def process_order(state: FryerState):
    if state['validation_passed']:
        print('Order processing initiated')
    return state

graph = StateGraph(FryerState)
graph.add_node('validate', validate_specs)
graph.add_node('order', process_order)
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph.set_entry_point('validate')
graph = graph.compile()