from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ControlState(TypedDict):
    raw_input: dict
    validated_spec: dict
    control_path: list

def validate_sensor_data(state: ControlState):
    data = state.get('raw_input', {})
    # Simulated validation logic
    is_valid = data.get('precision') > 0.001
    return {'validated_spec': {'valid': is_valid, 'timestamp': '2026-05-15'}}

def build_path(state: ControlState):
    return {'control_path': ['CALIBRATE', 'SIGNAL_SYNC', 'EXECUTE_MOVE']}

graph = StateGraph(ControlState)
graph.add_node('validator', validate_sensor_data)
graph.add_node('planner', build_path)
graph.add_edge('validator', 'planner')
graph.add_edge('planner', END)
graph.set_entry_point('validator')
graph = graph.compile()