from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnimalProcurementState(TypedDict):
    specifications: dict
    compliance_cleared: bool
    shipping_logistics: str

def validate_permits(state: AnimalProcurementState):
    state['compliance_cleared'] = 'CITES_permit' in state['specifications']
    return state

def check_logistics(state: AnimalProcurementState):
    if not state.get('compliance_cleared'):
        raise ValueError('Missing essential permits for live vertebrate transport.')
    state['shipping_logistics'] = 'Specialized Climate-Controlled Animal Transport'
    return state

graph = StateGraph(AnimalProcurementState)
graph.add_node('validate_permits', validate_permits)
graph.add_node('check_logistics', check_logistics)
graph.set_entry_point('validate_permits')
graph.add_edge('validate_permits', 'check_logistics')
graph.add_edge('check_logistics', END)
graph = graph.compile()
