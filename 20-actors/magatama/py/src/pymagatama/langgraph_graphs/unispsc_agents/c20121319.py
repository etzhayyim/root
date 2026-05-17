from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_sensor_specs(state: SensorState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if specs.get('ingress_protection_rating', 0) < 67:
        logs.append('Warning: IP rating below 67 for industrial use.')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def finalize_procurement(state: SensorState):
    return {'validation_logs': ['Procurement specification finalized and ready for review.']}

graph = StateGraph(SensorState)
graph.add_node('validate', validate_sensor_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()