from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity_level: float
    validation_checks: Annotated[List[str], operator.add]
    is_approved: bool

def validate_catalyst_purity(state: CatalystState):
    if state['purity_level'] >= 99.9:
        return {'validation_checks': ['High-purity standard met'], 'is_approved': True}
    return {'validation_checks': ['Purity insufficient for procurement'], 'is_approved': False}

def check_hazard_compliance(state: CatalystState):
    return {'validation_checks': ['Hazardous materials handling cleared']}

graph = StateGraph(CatalystState)
graph.add_node('validate_purity', validate_catalyst_purity)
graph.add_node('check_hazards', check_hazard_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_hazards')
graph.add_edge('check_hazards', END)
graph = graph.compile()