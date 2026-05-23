from typing import TypedDict
from langgraph.graph import StateGraph, END

class CymbalState(TypedDict):
    order_id: str
    specs: dict
    is_validated: bool

def validate_specs(state: CymbalState):
    required_keys = ['Alloy', 'Diameter', 'Weight']
    state['is_validated'] = all(k in state['specs'] for k in required_keys)
    return state

def check_quality(state: CymbalState):
    print(f'Checking acoustic specs for order {state['order_id']}')
    return 'validated' if state['is_validated'] else 'rejected'

graph = StateGraph(CymbalState)
graph.add_node('validate', validate_specs)
graph.add_edge('__start__', 'validate')
graph.add_edge('validate', END)
