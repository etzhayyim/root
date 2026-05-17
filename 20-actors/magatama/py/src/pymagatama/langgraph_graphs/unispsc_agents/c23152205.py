from typing import TypedDict
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: ServoState):
    required = ['CommunicationProtocol', 'InputVoltageRange']
    missing = [f for f in required if f not in state['specs']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: ServoState):
    return 'validate' if not state['validated'] else END

builder = StateGraph(ServoState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()