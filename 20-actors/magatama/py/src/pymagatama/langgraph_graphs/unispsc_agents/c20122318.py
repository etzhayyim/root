from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SwitchState(TypedDict):
    spec_requirements: dict
    validation_passed: bool
    error_log: list

def validate_switch_spec(state: SwitchState):
    specs = state['spec_requirements']
    errors = []
    if specs.get('load_capacity_amperes', 0) <= 0:
        errors.append('Invalid load capacity')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: SwitchState):
    return 'process_success' if state['validation_passed'] else 'flag_error'

def process_success(state: SwitchState):
    print('Switch specification verified for procurement.')
    return state

def flag_error(state: SwitchState):
    print(f'Validation failed: {state["error_log"]}')
    return state

graph = StateGraph(SwitchState)
graph.add_node('validate', validate_switch_spec)
graph.add_node('process_success', process_success)
graph.add_node('flag_error', flag_error)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process_success', END)
graph.add_edge('flag_error', END)

# Compile the graph
app = graph.compile()
