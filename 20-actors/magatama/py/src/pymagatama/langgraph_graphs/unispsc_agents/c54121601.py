from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GemstoneState(TypedDict):
    gem_id: str
    specifications: dict
    approved: bool

def validate_gem_specs(state: GemstoneState):
    # Simulate fine-grained validation of gemstone metadata
    required_keys = ['carat', 'clarity', 'color', 'origin_cert']
    all_present = all(k in state['specifications'] for k in required_keys)
    return {**state, 'approved': all_present}

def update_inventory(state: GemstoneState):
    print(f'Gem {state['gem_id']} logged into high-value registry.')
    return state

graph = StateGraph(GemstoneState)
graph.add_node('validate', validate_gem_specs)
graph.add_node('log', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph = graph.compile()