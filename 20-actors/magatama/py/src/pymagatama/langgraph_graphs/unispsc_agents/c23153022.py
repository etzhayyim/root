from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_specs(state: RobotState):
    specs = state['spec_data']
    result = 'Axis Accuracy' in specs and 'Payload Capacity' in specs
    return {'validation_result': result}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()