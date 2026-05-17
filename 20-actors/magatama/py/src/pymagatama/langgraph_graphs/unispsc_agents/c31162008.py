from typing import TypedDict
from langgraph.graph import StateGraph, END

class PinState(TypedDict):
    pin_specs: dict
    validation_passed: bool

def validate_specs(state: PinState):
    specs = state['pin_specs']
    passed = all([specs.get('hardness'), specs.get('dimensions')])
    return {'validation_passed': passed}

def route_by_validation(state: PinState):
    return 'process_order' if state['validation_passed'] else 'flag_error'

graph = StateGraph(PinState)
graph.add_node('validate', validate_specs)
graph.add_node('process_order', lambda x: x)
graph.add_node('flag_error', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process_order', END)
graph.add_edge('flag_error', END)

graph = graph.compile()