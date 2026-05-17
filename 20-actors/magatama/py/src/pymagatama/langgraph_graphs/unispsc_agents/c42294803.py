from typing import TypedDict
from langgraph.graph import StateGraph, END

class CystoState(TypedDict):
    serial_number: str
    sterility_status: bool
    validation_passed: bool

def validate_scope(state: CystoState):
    state['validation_passed'] = state.get('sterility_status') is True and len(state.get('serial_number', '')) > 0
    return state

def report_status(state: CystoState):
    print(f'Device {state['serial_number']} status: {state['validation_passed']}')
    return state

graph = StateGraph(CystoState)
graph.add_node('validate', validate_scope)
graph.add_node('report', report_status)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()