from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScrubberState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: ScrubberState):
    required = ['cleaning_path_width_cm', 'power_source']
    valid = all(k in state['specs'] for k in required)
    return {'approved': valid}

def route_by_power(state: ScrubberState):
    if state['specs'].get('power_source') == 'battery':
        return 'battery_inspection'
    return 'standard_inspection'

graph = StateGraph(ScrubberState)
graph.add_node('validate', validate_specs)
graph.add_node('battery_inspection', lambda s: s)
graph.add_node('standard_inspection', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_power)
graph.add_edge('battery_inspection', END)
graph.add_edge('standard_inspection', END)
graph = graph.compile()