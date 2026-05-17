from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SensorProcessState(TypedDict):
    sensor_id: str
    specs: dict
    validation_log: List[str]

def validate_sensor_specs(state: SensorProcessState):
    specs = state['specs']
    logs = []
    if specs.get('detection_range_mm', 0) <= 0:
        logs.append('Invalid detection range')
    if specs.get('protection_rating_ip', 'IP00') < 'IP65':
        logs.append('Insufficient IP rating for industrial use')
    return {'validation_log': logs}

def route_by_validation(state: SensorProcessState):
    if state['validation_log']:
        return 'error'
    return 'approve'

graph = StateGraph(SensorProcessState)
graph.add_node('validate', validate_sensor_specs)
graph.add_edge('validate', 'approve')
graph.set_entry_point('validate')
graph.set_finish_point('approve')

# Compilation
app = graph.compile()