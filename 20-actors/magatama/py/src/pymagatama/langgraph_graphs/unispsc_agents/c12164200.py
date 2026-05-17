from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    material_id: str
    analysis_results: Dict[str, Any]
    is_compliant: bool
    validation_log: List[str]

def validate_material_specs(state: MetalPowderState) -> MetalPowderState:
    # Simulate spectroscopic and laser diffraction analysis logic
    results = state.get('analysis_results', {})
    purity = results.get('purity', 0)
    state['is_compliant'] = purity >= 99.9
    state['validation_log'].append(f'Purity check: {purity}% compliant={state["is_compliant"]}')
    return state

def export_control_check(state: MetalPowderState) -> MetalPowderState:
    # Logic for dual-use verification
    state['validation_log'].append('Export control check initiated for high-purity metallic content.')
    return state

def build_metal_procurement_graph():
    graph = StateGraph(MetalPowderState)
    graph.add_node('validate', validate_material_specs)
    graph.add_node('export_check', export_control_check)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'export_check')
    graph.add_edge('export_check', END)
    return graph.compile()

graph = build_metal_procurement_graph()