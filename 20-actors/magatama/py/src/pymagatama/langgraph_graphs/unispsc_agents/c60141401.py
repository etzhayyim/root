from typing import TypedDict
from langgraph.graph import StateGraph, END

class CostumeState(TypedDict):
    item_id: str
    safety_check: bool
    compliance_validated: bool

def validate_material(state: CostumeState) -> CostumeState:
    print(f'Validating material safety for {state['item_id']}')
    state['safety_check'] = True
    return state

def check_compliance(state: CostumeState) -> CostumeState:
    print(f'Checking compliance for {state['item_id']}')
    state['compliance_validated'] = True
    return state

graph = StateGraph(CostumeState)
graph.add_node('material_check', validate_material)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('material_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('material_check')
graph = graph.compile()
