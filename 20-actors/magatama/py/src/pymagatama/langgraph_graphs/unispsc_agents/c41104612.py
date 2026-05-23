from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_risk: str

def validate_materials(state: FurnaceState):
    materials = state['spec_data'].get('materials', [])
    is_valid = all(m in ['Alumina', 'Quartz', 'Silicon Carbide'] for m in materials)
    return {'validation_passed': is_valid}

def check_compliance(state: FurnaceState):
    if state['spec_data'].get('max_temp', 0) > 1500:
        return {'compliance_risk': 'Dual-use high-temp materials'}
    return {'compliance_risk': 'Standard'}

graph = StateGraph(FurnaceState)
graph.add_node('material_check', validate_materials)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('material_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('material_check')
graph = graph.compile()
