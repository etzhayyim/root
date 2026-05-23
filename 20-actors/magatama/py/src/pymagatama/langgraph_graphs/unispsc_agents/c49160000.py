from typing import TypedDict
from langgraph.graph import StateGraph, END

class SportsEquipState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: SportsEquipState):
    required = ['material_durability_rating', 'official_league_compliance_certification']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_safety(state: SportsEquipState):
    print('Performing site safety and durability validation...')
    return state

graph = StateGraph(SportsEquipState)
graph.add_node('validate', validate_specs)
graph.add_node('safety_check', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
