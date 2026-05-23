from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ProcureState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], add_messages]

def validate_dielectric(state: ProcureState):
    spec = state['spec_data']
    if spec.get('dielectric_strength_kv', 0) < 5.0:
        return {'validation_log': ['Dielectric strength below minimum required 5.0kV']}
    return {'validation_log': ['Dielectric strength check passed']}

def check_thermal(state: ProcureState):
    spec = state['spec_data']
    if spec.get('thermal_resistance_index', 0) < 155:
        return {'validation_log': ['Thermal resistance insufficient for industrial insulation']}
    return {'validation_log': ['Thermal resilience compliant']}

graph = StateGraph(ProcureState)
graph.add_node('dielectric_check', validate_dielectric)
graph.add_node('thermal_check', check_thermal)
graph.add_edge('dielectric_check', 'thermal_check')
graph.set_entry_point('dielectric_check')
graph.add_edge('thermal_check', END)
graph = graph.compile()
