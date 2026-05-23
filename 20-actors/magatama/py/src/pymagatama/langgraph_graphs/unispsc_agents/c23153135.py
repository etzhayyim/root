from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    actuator_id: str
    torque_rating: float
    status: str
    validation_log: Annotated[List[str], operator.add]

def validate_torque(state: ActuatorState):
    log = []
    if state['torque_rating'] <= 0:
        log.append('Invalid torque rating detected')
        return {'status': 'FAILED', 'validation_log': log}
    log.append('Torque rating validated')
    return {'status': 'VALIDATED', 'validation_log': log}

def perform_lifecycle_check(state: ActuatorState):
    log = ['Lifecycle safety check performed']
    return {'validation_log': log}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_torque)
graph.add_node('lifecycle', perform_lifecycle_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'lifecycle')
graph.add_edge('lifecycle', END)

compiled_graph = graph.compile()
