from typing import TypedDict
from langgraph.graph import StateGraph, END

class PagerConfigState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_frequency(state: PagerConfigState):
    freq = state['spec_data'].get('frequency_range_mhz', 0)
    valid = 100 <= freq <= 900
    return {'validated': valid, 'error_log': [] if valid else ['Frequency out of range']}

def deploy_logic(state: PagerConfigState):
    return state

graph = StateGraph(PagerConfigState)
graph.add_node('validate', validate_frequency)
graph.add_node('deploy', deploy_logic)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()
