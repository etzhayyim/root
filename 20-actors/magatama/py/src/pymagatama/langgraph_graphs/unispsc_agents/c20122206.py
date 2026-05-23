from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    part_number: str
    specs: dict
    is_validated: bool
    validation_log: List[str]

def validate_specs(state: ActuatorState):
    log = []
    if state['specs'].get('torque_nm', 0) > 0:
        log.append('Torque validated')
    return {'is_validated': True, 'validation_log': log}

def process_deployment(state: ActuatorState):
    return {'validation_log': state['validation_log'] + ['Deployment ready']}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', process_deployment)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()
