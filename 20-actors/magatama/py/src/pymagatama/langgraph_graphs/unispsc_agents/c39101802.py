from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class LampGlassState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_thermal_specs(state: LampGlassState):
    glass_specs = state['spec_data']
    valid = glass_specs.get('thermal_expansion', 0) < 10.0
    return {'validation_results': [f'Thermal expansion valid: {valid}'], 'is_compliant': valid}

def finalize_procurement(state: LampGlassState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(LampGlassState)
graph.add_node('validate_thermal', validate_thermal_specs)
graph.add_node('finalizer', finalize_procurement)
graph.add_edge('validate_thermal', 'finalizer')
graph.add_edge('finalizer', END)
graph.set_entry_point('validate_thermal')
graph = graph.compile()
