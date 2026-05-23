from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    part_number: str
    torque_requirements: float
    validation_status: bool
    errors: List[str]

def validate_torque(state: ActuatorState):
    is_valid = state['torque_requirements'] > 0
    return {'validation_status': is_valid}

def process_actuator_assembly(state: ActuatorState):
    if not state['validation_status']:
        return {'errors': ['Invalid torque requirements']}
    return {'errors': []}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_torque)
graph.add_node('assemble', process_actuator_assembly)
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph.set_entry_point('validate')
graph = graph.compile()
