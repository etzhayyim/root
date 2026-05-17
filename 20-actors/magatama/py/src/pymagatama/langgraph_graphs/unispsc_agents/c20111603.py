from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: HydraulicState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if specs.get('maximum_operating_pressure_mpa', 0) > 35.0:
        logs.append('Warning: Extreme pressure rating detected.')
    if not specs.get('seal_material_specification'):
        compliant = False
        logs.append('Error: Missing mandatory seal material specs.')
    return {'validation_log': logs, 'is_compliant': compliant}

def finalize_procurement(state: HydraulicState):
    return {'validation_log': ['Procurement documentation generated successfully.']}

graph = StateGraph(HydraulicState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()