from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity_level: float
    safety_score: float
    compliance_validated: bool
    history: List[str]

def validate_purity(state: ChemicalState):
    if state['purity_level'] >= 0.98:
        return {'compliance_validated': True, 'history': state['history'] + ['Purity OK']}
    return {'compliance_validated': False, 'history': state['history'] + ['Purity Low']}

def safety_check(state: ChemicalState):
    if state['safety_score'] > 8.5:
        return {'history': state['history'] + ['Safety Certified']}
    return {'history': state['history'] + ['Safety Review Required']}

graph = StateGraph(ChemicalState)
graph.add_node('purity_check', validate_purity)
graph.add_node('safety_check', safety_check)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()