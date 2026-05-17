from typing import TypedDict
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: ServoState):
    required = ['Torque', 'Voltage', 'Protocol']
    missing = [f for f in required if f not in state['specs']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: ServoState):
    return 'process' if state['validated'] else 'reject'

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.add_node('reject', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph.add_edge('reject', END)
graph = graph.compile()