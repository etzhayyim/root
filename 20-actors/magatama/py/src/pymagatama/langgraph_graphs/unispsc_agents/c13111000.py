from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class OreState(TypedDict):
    material_type: str
    purity_level: float
    origin_country: str
    is_verified: bool
    compliance_tags: List[str]

def validate_purity(state: OreState) -> OreState:
    if state['purity_level'] < 95.0:
        state['compliance_tags'].append('low_purity_alert')
    state['is_verified'] = True
    return state

def check_sanctions(state: OreState) -> OreState:
    if state['origin_country'] in ['restricted_zone_a', 'restricted_zone_b']:
        state['compliance_tags'].append('sanction_risk')
    return state

graph = StateGraph(OreState)
graph.add_node('validate', validate_purity)
graph.add_node('sanction_check', check_sanctions)
graph.add_edge('validate', 'sanction_check')
graph.add_edge('sanction_check', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
