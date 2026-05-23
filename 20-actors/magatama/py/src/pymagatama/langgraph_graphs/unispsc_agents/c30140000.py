from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class InsulationState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_thermal_specs(state: InsulationState):
    conductivity = state['spec_data'].get('thermal_conductivity', 1.0)
    compliant = conductivity < 0.05
    return {'is_compliant': compliant, 'validation_log': ['Thermal check passed' if compliant else 'High conductivity detected']}

def check_fire_rating(state: InsulationState):
    rating = state['spec_data'].get('fire_rating', 'None')
    return {'validation_log': state['validation_log'] + [f'Fire rating verified: {rating}']}

graph = StateGraph(InsulationState)
graph.add_node('validate_thermal', validate_thermal_specs)
graph.add_node('check_fire', check_fire_rating)
graph.set_entry_point('validate_thermal')
graph.add_edge('validate_thermal', 'check_fire')
graph.add_edge('check_fire', END)
graph = graph.compile()
