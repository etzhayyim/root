from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    material_spec: str
    bonding_strength: float
    inspection_passed: bool
    history: List[str]

def validate_materials(state: ProcurementState):
    passed = state['material_spec'] in ['ASTM-A514', 'JIS-SM490']
    return {'inspection_passed': passed, 'history': ['Material validated']}

def check_bonding(state: ProcurementState):
    passed = state['bonding_strength'] >= 450.0
    return {'inspection_passed': state['inspection_passed'] and passed, 'history': state['history'] + ['Bonding tested']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('bonding', check_bonding)
graph.set_entry_point('validate')
graph.add_edge('validate', 'bonding')
graph.add_edge('bonding', END)
graph = graph.compile()
