from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    purity_level: float
    origin: str
    is_compliant: bool
    validation_log: List[str]

def validate_purity(state: MineralState):
    compliant = state['purity_level'] >= 99.5
    return {'is_compliant': compliant, 'validation_log': [f'Purity check: {compliant}']}

def check_sanctions(state: MineralState):
    restricted = state['origin'] in ['CountryA', 'CountryB']
    return {'is_compliant': not restricted, 'validation_log': state['validation_log'] + [f'Sanctions check: {not restricted}']}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('sanctions', check_sanctions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sanctions')
graph.add_edge('sanctions', END)
graph = graph.compile()