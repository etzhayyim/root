from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    commodity_code: str
    purity_level: float
    safety_clearance: bool
    log_path: List[str]

def validate_purity(state: ChemicalState):
    is_pure = state['purity_level'] >= 99.999
    return {'safety_clearance': is_pure, 'log_path': state['log_path'] + ['purity_verified']}

def check_compliance(state: ChemicalState):
    return {'safety_clearance': state['safety_clearance'] and True, 'log_path': state['log_path'] + ['compliance_checked']}

graph = StateGraph(ChemicalState)
graph.add_node('purity_check', validate_purity)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('purity_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('purity_check')
compiled_graph = graph.compile()
