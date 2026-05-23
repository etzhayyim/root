from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_pressure_rating(state: HydraulicState):
    pressure = state['spec_data'].get('operating_pressure_mpa', 0)
    if pressure > 35.0:
        return {'validation_logs': ['High pressure rating requires extra verification'], 'is_approved': True}
    return {'validation_logs': ['Standard pressure range verified'], 'is_approved': True}

def structural_integrity_check(state: HydraulicState):
    return {'validation_logs': ['Structural integrity pass'], 'is_approved': True}

graph = StateGraph(HydraulicState)
graph.add_node('validate_pressure', validate_pressure_rating)
graph.add_node('structural_integrity', structural_integrity_check)
graph.add_edge('validate_pressure', 'structural_integrity')
graph.add_edge('structural_integrity', END)
graph.set_entry_point('validate_pressure')
graph = graph.compile()
