from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    resin_id: str
    specifications: dict
    is_compliant: bool
    validation_log: List[str]

def validate_resin_specs(state: ResinState) -> ResinState:
    specs = state['specifications']
    logs = state.get('validation_log', [])
    # Specialized validation logic for high-performance resins
    is_valid = specs.get('thermal_decomposition_temp_c', 0) > 300
    compliance = 'PASS' if is_valid else 'FAIL'
    logs.append(f'Thermal validation: {compliance}')
    return {'is_compliant': is_valid, 'validation_log': logs}

def approve_procurement(state: ResinState) -> ResinState:
    return {'validation_log': state.get('validation_log', []) + ['Procurement approved']}

workflow = StateGraph(ResinState)
workflow.add_node('validate', validate_resin_specs)
workflow.add_node('approve', approve_procurement)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', lambda s: 'approve' if s['is_compliant'] else END, {'approve': 'approve'})
workflow.add_edge('approve', END)
graph = workflow.compile()
