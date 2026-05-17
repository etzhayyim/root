from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeaterSpecState(TypedDict):
    voltage: int
    temp_range: tuple
    validated: bool

def validate_specs(state: HeaterSpecState):
    is_valid = state['voltage'] in [110, 220, 440] and state['temp_range'][1] > 0
    return {'validated': is_valid}

def check_compliance(state: HeaterSpecState):
    print(f'Compliance check: {state["validated"]}')
    return 'end'

graph = StateGraph(HeaterSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()