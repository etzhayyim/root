from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BathToyState(TypedDict):
    product_name: str
    compliance_docs: List[str]
    safety_check_passed: bool

def validate_safety_data(state: BathToyState):
    required = ['ASTM F963', 'BPA-free']
    passed = all(doc in state['compliance_docs'] for doc in required)
    return {"safety_check_passed": passed}

def inspect_mold_risk(state: BathToyState):
    print(f'Checking drainage and mold risk for {state['product_name']}')
    return {"safety_check_passed": state['safety_check_passed']}

graph = StateGraph(BathToyState)
graph.add_node('safety', validate_safety_data)
graph.add_node('mold_inspection', inspect_mold_risk)
graph.set_entry_point('safety')
graph.add_edge('safety', 'mold_inspection')
graph.add_edge('mold_inspection', END)
graph = graph.compile()