from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class RobotHandState(TypedDict):
    payload: float
    gripper_config: dict
    validation_results: list[str]

def validate_payload(state: RobotHandState):
    limit = 5.0
    if state['payload'] > limit:
        return {'validation_results': ['Payload exceeds safety limit for this class']}
    return {'validation_results': ['Payload valid']}

def configure_gripper(state: RobotHandState):
    # Simulate hardware interface configuration
    return {'validation_results': state['validation_results'] + ['Interface protocol configured']}

graph = StateGraph(RobotHandState)
graph.add_node('validate', validate_payload)
graph.add_node('configure', configure_gripper)
graph.set_entry_point('validate')
graph.add_edge('validate', 'configure')
graph.add_edge('configure', END)
compile_graph = graph.compile()