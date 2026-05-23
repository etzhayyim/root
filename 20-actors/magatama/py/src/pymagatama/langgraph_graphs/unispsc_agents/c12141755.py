from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class RareEarthState(TypedDict):
    purity: float
    impurities: dict
    approved: bool
    logs: Annotated[List[str], operator.add]

def validate_purity(state: RareEarthState) -> dict:
    is_pure = state['purity'] >= 99.99
    return {'approved': is_pure, 'logs': ['Purity validated']}

def check_compliance(state: RareEarthState) -> dict:
    risk_found = any(val > 10 for val in state['impurities'].values())
    return {'approved': not risk_found, 'logs': ['Compliance checked']}

graph = StateGraph(RareEarthState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
