from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    material_spec: dict
    validation_passed: bool

def validate_specs(state: State):
    req_keys = ['thickness', 'material', 'length']
    passed = all(k in state['material_spec'] for k in req_keys)
    return {'validation_passed': passed}

def process_procurement(state: State):
    print('Procurement request processed successfully.')
    return {}

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()