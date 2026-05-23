from typing import TypedDict
from langgraph.graph import StateGraph, END
class GasketState(TypedDict):
    spec_sheet: dict
    validation_passed: bool
def validate_materials(state: GasketState):
    material = state['spec_sheet'].get('material')
    is_valid = material in ['EPDM', 'PTFE', 'Nitrile', 'Silicone']
    return {'validation_passed': is_valid}
def check_compliance(state: GasketState):
    pressure = state['spec_sheet'].get('pressure', 0)
    return {'validation_passed': state['validation_passed'] and pressure > 0}
graph = StateGraph(GasketState)
graph.add_node('material_check', validate_materials)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
