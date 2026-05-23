from typing import TypedDict
from langgraph.graph import StateGraph, END

class TitaniumProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_licensing_required: bool

def validate_material_specs(state: TitaniumProcurementState):
    # Business logic for verifying metallurgical grades (e.g., Gr2, Gr5)
    grade = state['spec_data'].get('grade')
    return {'validation_passed': grade in ['Grade 2', 'Grade 5']}

def check_export_compliance(state: TitaniumProcurementState):
    # Dual-use export control assessment script
    return {'export_licensing_required': True}

graph = StateGraph(TitaniumProcurementState)
graph.add_node('validate', validate_material_specs)
graph.add_node('compliance', check_export_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
