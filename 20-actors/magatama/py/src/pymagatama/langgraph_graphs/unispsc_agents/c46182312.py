from typing import TypedDict
from langgraph.graph import StateGraph, END

class DescenderState(TypedDict):
    load_capacity: float
    rope_diameter: float
    is_certified: bool
    approved: bool

def validate_specs(state: DescenderState):
    if state['load_capacity'] >= 150 and state['rope_diameter'] >= 9.0 and state['is_certified']:
        return {'approved': True}
    return {'approved': False}

def final_decision(state: DescenderState):
    print(f'Approval Status: {state['approved']}')

graph = StateGraph(DescenderState)
graph.add_node('validate', validate_specs)
graph.add_node('record', final_decision)
graph.add_edge('validate', 'record')
graph.add_edge('record', END)
graph.set_entry_point('validate')
graph = graph.compile()
