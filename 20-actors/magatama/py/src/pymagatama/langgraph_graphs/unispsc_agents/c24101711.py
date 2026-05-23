from typing import TypedDict
from langgraph.graph import StateGraph, END

class TurntableState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_load_capacity(state: TurntableState):
    load = state['specs'].get('load_capacity', 0)
    state['validation_passed'] = load > 0
    return state

def check_precision(state: TurntableState):
    precision = state['specs'].get('precision', 1.0)
    state['validation_passed'] = state['validation_passed'] and (precision < 0.5)
    return state

graph = StateGraph(TurntableState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_precision', check_precision)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_precision')
graph.add_edge('check_precision', END)
app = graph.compile()
