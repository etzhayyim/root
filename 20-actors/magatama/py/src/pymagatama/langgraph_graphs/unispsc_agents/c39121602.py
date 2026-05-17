from typing import TypedDict
from langgraph.graph import StateGraph, END

class CircuitBreakerState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: CircuitBreakerState):
    required = ['Rated Current', 'Rated Voltage', 'Interrupting Capacity']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: CircuitBreakerState):
    return 'process' if state['validated'] else END

def process_breaker(state: CircuitBreakerState):
    print('Processing validated magnetic circuit breaker specs.')
    return state

builder = StateGraph(CircuitBreakerState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_breaker)
builder.set_entry_point('validate')
builder.add_conditional_edges('validate', route_by_validation)
builder.add_edge('process', END)
graph = builder.compile()