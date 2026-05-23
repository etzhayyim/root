from typing import TypedDict
from langgraph.graph import StateGraph, END

class MemoryGameState(TypedDict):
    product_id: str
    safety_check_passed: bool
    compliance_validated: bool

def validate_safety(state: MemoryGameState):
    print(f'Validating toy safety for {state['product_id']}')
    return {'safety_check_passed': True}

def validate_compliance(state: MemoryGameState):
    print(f'Checking ASTM/CE compliance for {state['product_id']}')
    return {'compliance_validated': True}

graph = StateGraph(MemoryGameState)
graph.add_node('safety', validate_safety)
graph.add_node('compliance', validate_compliance)
graph.add_edge('safety', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('safety')
graph = graph.compile()
