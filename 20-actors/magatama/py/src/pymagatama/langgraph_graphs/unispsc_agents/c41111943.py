from typing import TypedDict
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: SensorState):
    required = ['measurement_range', 'accuracy_tolerance']
    compliance = all(k in state['spec_data'] for k in required)
    return { "validation_results": ["Range and Accuracy check"], "is_compliant": compliance }

def process_sensor(state: SensorState):
    print("Processing sensor procurement specification...")
    return state

graph = StateGraph(SensorState)
graph.add_node("validate", validate_specs)
graph.add_node("process", process_sensor)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()
