from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterBathState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: WaterBathState):
    s = state['specs']
    valid = all(k in s for k in ['temp_range', 'rpm', 'capacity'])
    return {'validated': valid, 'error': None if valid else 'Missing required specs'}

def process_procurement(state: WaterBathState):
    print('Procurement logic for Water Bath initiated...')
    return {'validated': True}

graph = StateGraph(WaterBathState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()