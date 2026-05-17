from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HardwareState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: HardwareState):
    required = ['material_grade', 'load_capacity_rating']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing specs'}

def process_procurement(state: HardwareState):
    return {'validated': True}

graph = StateGraph(HardwareState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()