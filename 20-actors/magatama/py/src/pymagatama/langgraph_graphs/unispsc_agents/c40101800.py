from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict
class HeatingProcurementState(TypedDict):
    spec_data: Dict[str, Any]
    validation_results: Dict[str, bool]
    is_compliant: bool
def validate_specs(state: HeatingProcurementState):
    specs = state['spec_data']
    valid = all(k in specs for k in ['capacity', 'safety_std'])
    return {'validation_results': {'specs': valid}, 'is_compliant': valid}
def check_compliance(state: HeatingProcurementState):
    return {'is_compliant': state['validation_results']['specs']}
graph = StateGraph(HeatingProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()