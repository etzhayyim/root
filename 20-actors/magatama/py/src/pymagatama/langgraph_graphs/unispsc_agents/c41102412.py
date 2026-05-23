from typing import TypedDict
from langgraph.graph import StateGraph, END

class BlowerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_airflow(state: BlowerState):
    wattage = state['spec_data'].get('wattage', 0)
    state['validation_passed'] = wattage > 0 and wattage < 5000
    return state

def check_compliance(state: BlowerState):
    return 'pass' if state['validation_passed'] else 'fail'

graph = StateGraph(BlowerState)
graph.add_node('validate', validate_airflow)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
