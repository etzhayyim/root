from typing import TypedDict
from langgraph.graph import StateGraph, END

class WetsuitState(TypedDict):
    spec: dict
    approved: bool

def validate_materials(state: WetsuitState):
    print('Validating neoprene quality and thickness...')
    state['approved'] = state['spec'].get('thickness_mm', 0) > 0
    return state

def check_compliance(state: WetsuitState):
    print('Checking safety standards compliance...')
    return state

graph = StateGraph(WetsuitState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()