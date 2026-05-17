import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class LevelSwitchState(TypedDict):
    spec_data: dict
    validation_log: Annotated[list, operator.add]
    is_compliant: bool

def validate_pressure_specs(state: LevelSwitchState):
    pressure = state['spec_data'].get('pressure_rating', 0)
    if pressure > 0:
        return {'validation_log': ['Pressure rating verified'], 'is_compliant': True}
    return {'validation_log': ['Invalid pressure rating'], 'is_compliant': False}

graph = StateGraph(LevelSwitchState)
graph.add_node('validate', validate_pressure_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()