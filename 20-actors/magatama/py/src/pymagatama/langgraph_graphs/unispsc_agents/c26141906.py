from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    device_id: str
    radiation_level: float
    compliance_cleared: bool

def validate_safety_protocols(state: State):
    if state['radiation_level'] > 0.05:
        return {'compliance_cleared': False}
    return {'compliance_cleared': True}

def process_deployment(state: State):
    print(f'Deploying device {state['device_id']} with safety validation: {state['compliance_cleared']}')
    return state

graph = StateGraph(State)
graph.add_node('safety_check', validate_safety_protocols)
graph.add_node('deployment', process_deployment)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'deployment')
graph.add_edge('deployment', END)
graph = graph.compile()