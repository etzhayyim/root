from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeaterSpec(TypedDict):
    voltage: int
    wattage: int
    safety_certified: bool

def validate_specs(state: HeaterSpec):
    if state['wattage'] > 5000: return 'high_power_audit'
    return 'standard_procurement'

def high_power_audit(state: HeaterSpec): return {'status': 'requires_industrial_clearance'}
def standard_procurement(state: HeaterSpec): return {'status': 'approved'}

graph = StateGraph(HeaterSpec)
graph.add_node('validate', validate_specs)
graph.add_node('high_power_audit', high_power_audit)
graph.add_node('standard_procurement', standard_procurement)
graph.set_entry_point('validate')
graph.add_edge('high_power_audit', END)
graph.add_edge('standard_procurement', END)
graph = graph.compile()