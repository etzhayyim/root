from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MathProcurementState(TypedDict):
    item_name: str
    safety_certs: List[str]
    approved: bool

def validate_safety_certs(state: MathProcurementState):
    required = ['ASTM F963', 'EN71']
    state['approved'] = all(cert in state['safety_certs'] for cert in required)
    return state

def check_material(state: MathProcurementState):
    print(f'Checking material safety for {state['item_name']}')
    return state

graph = StateGraph(MathProcurementState)
graph.add_node('safety_check', validate_safety_certs)
graph.add_node('material_check', check_material)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()