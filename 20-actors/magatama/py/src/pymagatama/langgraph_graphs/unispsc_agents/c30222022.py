from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BreakwaterState(TypedDict):
    material_specs: dict
    compliance_checks: List[str]
    is_approved: bool

def validate_specs(state: BreakwaterState):
    state['is_approved'] = 'Strength' in state['material_specs'] and 'Durability' in state['material_specs']
    return state

def log_procurement(state: BreakwaterState):
    print(f'Procurement approved: {state['is_approved']}')
    return state

graph = StateGraph(BreakwaterState)
graph.add_node('validate', validate_specs)
graph.add_node('log', log_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph = graph.compile()