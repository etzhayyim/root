from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    purity_level: float
    status: str

def validate_quality(state: DrugState):
    if state['purity_level'] >= 99.0:
        return {'status': 'COMPLIANT'}
    return {'status': 'REJECTED'}

def update_inventory(state: DrugState):
    print(f'Logging batch {state['batch_id']} to pharmaceutical registry.')
    return {'status': 'REGISTERED'}

graph = StateGraph(DrugState)
graph.add_node('validate', validate_quality)
graph.add_node('log', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph = graph.compile()
