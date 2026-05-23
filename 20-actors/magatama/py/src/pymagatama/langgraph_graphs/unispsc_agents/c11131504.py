from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CatalystState(TypedDict):
    commodity_code: str
    purity_level: float
    safety_check_passed: bool
    history: Annotated[List[str], operator.add]

def validate_purity(state: CatalystState):
    # Simulate fine-grained purity validation for industrial catalysts
    is_valid = state['purity_level'] >= 0.99
    return {'safety_check_passed': is_valid, 'history': ['Validated chemical purity']}

def safety_protocol_check(state: CatalystState):
    if state['safety_check_passed']:
        return 'secure'
    return 'quarantine'

builder = StateGraph(CatalystState)
builder.add_node('purity_check', validate_purity)
builder.set_entry_point('purity_check')
builder.add_edge('purity_check', END)
graph = builder.compile()
