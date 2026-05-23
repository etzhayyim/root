from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    validated: bool

def validate_solar_specs(state: LightingState):
    specs = state['spec_data']
    is_valid = all([specs.get('lumens', 0) > 0, specs.get('battery_capacity', 0) > 0])
    return {'validated': is_valid}

workflow = StateGraph(LightingState)
workflow.add_node('validate', validate_solar_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
