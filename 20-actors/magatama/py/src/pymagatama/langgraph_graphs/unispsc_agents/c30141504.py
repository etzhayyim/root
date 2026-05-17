from typing import TypedDict
from langgraph.graph import StateGraph, END

class InsulationState(TypedDict):
    r_value: float
    material_type: str
    compliance_checked: bool

def validate_thermal_specs(state: InsulationState):
    if state['r_value'] < 3.0:
        print('R-value below requirement')
    return {'compliance_checked': True}

graph = StateGraph(InsulationState)
graph.add_node('validate', validate_thermal_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()