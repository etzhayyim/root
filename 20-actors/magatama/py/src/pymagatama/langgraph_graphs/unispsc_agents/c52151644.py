from typing import TypedDict
from langgraph.graph import StateGraph, END

class SprayProcurementState(TypedDict):
    material_safety_data: dict
    performance_test_results: dict
    is_compliant: bool

def validate_material(state: SprayProcurementState):
    # Simulate material compliance check
    state['is_compliant'] = state['material_safety_data'].get('bpa_free', False)
    return state

def validate_performance(state: SprayProcurementState):
    # Simulate spray mechanism QC
    if state['performance_test_results'].get('leak_rate', 1.0) < 0.05:
        state['is_compliant'] = True
    else:
        state['is_compliant'] = False
    return state

workflow = StateGraph(SprayProcurementState)
workflow.add_node('check_material', validate_material)
workflow.add_node('check_performance', validate_performance)
workflow.add_edge('check_material', 'check_performance')
workflow.add_edge('check_performance', END)
workflow.set_entry_point('check_material')
graph = workflow.compile()
