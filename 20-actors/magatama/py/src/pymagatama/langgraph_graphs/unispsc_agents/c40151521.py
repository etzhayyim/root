from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_pump_specs(state: PumpState):
    specs = state['spec_data']
    required = ['flow_rate', 'pressure', 'material']
    compliant = all(key in specs for key in required) and specs['pressure'] > 0
    return {'is_compliant': compliant}

def pump_procurement_workflow():
    graph = StateGraph(PumpState)
    graph.add_node('validation', validate_pump_specs)
    graph.set_entry_point('validation')
    graph.add_edge('validation', END)
    return graph.compile()

graph = pump_procurement_workflow()