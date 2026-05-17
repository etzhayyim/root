from typing import TypedDict
from langgraph.graph import StateGraph, END

class EntomologyGraphState(TypedDict):
    facility_specs: dict
    validation_passed: bool

def validate_environmental_specs(state: EntomologyGraphState):
    temp = state['facility_specs'].get('temperature', 0)
    state['validation_passed'] = 15 <= temp <= 35
    return state

def decision_node(state: EntomologyGraphState):
    return 'pass' if state['validation_passed'] else 'fail'

graph = StateGraph(EntomologyGraphState)
graph.add_node('validate', validate_environmental_specs)
graph.add_node('pass', lambda state: state)
graph.add_node('fail', lambda state: state)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', decision_node, {'pass': 'pass', 'fail': 'fail'})
graph.add_edge('pass', END)
graph.add_edge('fail', END)
graph.compile()