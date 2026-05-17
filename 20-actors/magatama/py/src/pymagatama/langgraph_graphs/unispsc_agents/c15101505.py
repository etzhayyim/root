from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralFuelState(TypedDict):
    commodity_code: str
    origin: str
    purity_level: float
    compliance_check: bool
    validation_logs: List[str]

def validate_purity(state: MineralFuelState):
    is_valid = state['purity_level'] > 0.95
    return {'compliance_check': is_valid, 'validation_logs': ['Purity check passed' if is_valid else 'Purity below threshold']}

def check_sanctions(state: MineralFuelState):
    restricted = ['restricted_zone_a', 'restricted_zone_b']
    passed = state['origin'] not in restricted
    return {'compliance_check': passed, 'validation_logs': state['validation_logs'] + ['Sanctions check cleared' if passed else 'Sanctions violation detected']}

graph = StateGraph(MineralFuelState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_sanctions', check_sanctions)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_sanctions')
graph.add_edge('check_sanctions', END)
compiled_graph = graph.compile()