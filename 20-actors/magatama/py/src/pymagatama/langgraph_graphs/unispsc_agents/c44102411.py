from typing import TypedDict
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    label_width: float
    is_electric: bool
    validation_passed: bool

def validate_specs(state: DispenserState):
    if state['label_width'] > 0:
        state['validation_passed'] = True
    return state

def check_electrical(state: DispenserState):
    print(f'Checking power requirements for electric: {state['is_electric']}')
    return 'end'

graph = StateGraph(DispenserState)
graph.add_node('validate', validate_specs)
graph.add_node('power_check', check_electrical)
graph.set_entry_point('validate')
graph.add_edge('validate', 'power_check')
graph.add_edge('power_check', END)
graph = graph.compile()
