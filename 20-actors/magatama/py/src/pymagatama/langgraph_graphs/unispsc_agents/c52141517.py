from typing import TypedDict
from langgraph.graph import StateGraph, END

class PopcornSpecState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_electrical_safety(state: PopcornSpecState):
    # Simulate PSE/UL compliance check
    cert = state['spec_data'].get('certification')
    return {'is_compliant': cert in ['PSE', 'UL', 'CE']}

def process_procurement(state: PopcornSpecState):
    print(f'Processing procurement with compliance: {state['is_compliant']}')
    return state

graph = StateGraph(PopcornSpecState)
graph.add_node('safety_check', validate_electrical_safety)
graph.add_node('final_process', process_procurement)
graph.add_edge('safety_check', 'final_process')
graph.add_edge('final_process', END)
graph.set_entry_point('safety_check')

compiled_graph = graph.compile()