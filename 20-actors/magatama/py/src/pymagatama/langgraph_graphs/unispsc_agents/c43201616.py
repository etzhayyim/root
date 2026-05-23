from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_redundancy(state: StorageState):
    redundancy = state['specs'].get('redundancy', False)
    if not redundancy: state['errors'].append('Redundancy feature required.')
    return {'validation_passed': redundancy}

def check_capacity(state: StorageState):
    capacity = state['specs'].get('capacity_tb', 0)
    if capacity < 10: state['errors'].append('Insufficient storage capacity.')
    return {'validation_passed': state['validation_passed'] and capacity >= 10}

graph = StateGraph(StorageState)
graph.add_node('validate_redundancy', validate_redundancy)
graph.add_node('check_capacity', check_capacity)
graph.set_entry_point('validate_redundancy')
graph.add_edge('validate_redundancy', 'check_capacity')
graph.add_edge('check_capacity', END)
graph = graph.compile()
