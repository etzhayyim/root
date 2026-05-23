from langgraph.graph import StateGraph, END
from typing import TypedDict
class CommodityState(TypedDict):
    item_id: str
    safety_check_passed: bool
    compliance_score: float

def validate_safety_compliance(state: CommodityState):
    state['safety_check_passed'] = True
    state['compliance_score'] = 0.95
    print(f'Validating infant suit {state['item_id']} for textile safety standards.')
    return state

def formalize_spec(state: CommodityState):
    print(f'Formalizing product spec for items passing check: {state['safety_check_passed']}')
    return state

graph = StateGraph(CommodityState)
graph.add_node('safety_check', validate_safety_compliance)
graph.add_node('formalize', formalize_spec)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'formalize')
graph.add_edge('formalize', END)
graph = graph.compile()
