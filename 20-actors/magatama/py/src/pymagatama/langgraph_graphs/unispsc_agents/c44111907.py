from typing import TypedDict
from langgraph.graph import StateGraph, END

class BulletinState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: BulletinState):
    required = ['dimensions', 'material', 'mounting']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid}

def process_procurement(state: BulletinState):
    return {'validated': True}

graph = StateGraph(BulletinState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

app = graph.compile()
