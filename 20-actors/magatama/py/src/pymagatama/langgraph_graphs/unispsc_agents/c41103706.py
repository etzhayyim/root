from langgraph.graph import StateGraph, END
from typing import TypedDict
class WaterBathState(TypedDict):
    spec_data: dict
    is_compliant: bool
def validate_specs(state: WaterBathState):
    temp_range = state['spec_data'].get('TemperatureRangeCelsius', 0)
    state['is_compliant'] = temp_range > 0
    return state
def finalize_order(state: WaterBathState):
    return {'is_compliant': True}
graph = StateGraph(WaterBathState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
