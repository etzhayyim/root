from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ZincProcurementState(TypedDict):
    material_spec: dict
    validation_results: List[str]
    is_compliant: bool

def validate_zinc_quality(state: ZincProcurementState):
    spec = state['material_spec']
    results = []
    if spec.get('coating_thickness', 0) < 50:
        results.append('Coating thickness below minimum threshold')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def update_compliance_status(state: ZincProcurementState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(ZincProcurementState)
graph.add_node('validate', validate_zinc_quality)
graph.add_node('finalize', update_compliance_status)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()