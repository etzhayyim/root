from typing import TypedDict
from langgraph.graph import StateGraph, END

class StackProcurementState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_report: str

def validate_structural_specs(state: StackProcurementState):
    specs = state['spec_data']
    compliant = all(k in specs for k in ['seismic_rating', 'material_grade'])
    return {'is_compliant': compliant, 'validation_report': 'Validated' if compliant else 'Missing specs'}

def finalize_order(state: StackProcurementState):
    return {'validation_report': 'Order ready for procurement'}

graph = StateGraph(StackProcurementState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
