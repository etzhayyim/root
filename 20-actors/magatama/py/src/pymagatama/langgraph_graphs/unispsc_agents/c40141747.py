from langgraph.graph import StateGraph, END
from typing import TypedDict

class GreaseTrapState(TypedDict):
    capacity: float
    material: str
    compliance_checked: bool

def validate_specs(state: GreaseTrapState):
    if state['capacity'] > 0 and state['material'] in ['Stainless Steel', 'Polyethylene']:
        return {'compliance_checked': True}
    return {'compliance_checked': False}

def process_workflow(state: GreaseTrapState):
    print(f'Processing grease trap with capacity: {state['capacity']}')
    return state

graph = StateGraph(GreaseTrapState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
