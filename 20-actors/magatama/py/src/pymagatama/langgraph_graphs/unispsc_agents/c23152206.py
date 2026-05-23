from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    specs: dict
    validation_status: str
    compliance_risk: str

def validate_thermal_specs(state: FurnaceState):
    temp = state['specs'].get('temp', 0)
    if temp > 1500: return {'validation_status': 'high_temp_certified', 'compliance_risk': 'dual-use-export-control'}
    return {'validation_status': 'standard_certified', 'compliance_risk': 'none'}

graph = StateGraph(FurnaceState)
graph.add_node('validate', validate_thermal_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
