from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_torque(state: ActuatorState):
    torque = state['spec_data'].get('torque_rating', 0)
    result = 'Torque sufficient' if torque > 0 else 'Torque invalid'
    return {'validation_results': [result]}

def validate_ip_rating(state: ActuatorState):
    rating = state['spec_data'].get('ip_rating', 'IP00')
    result = f'IP rating {rating} verified' if rating >= 'IP54' else 'IP rating insufficient'
    return {'validation_results': [result]}

def finalize_check(state: ActuatorState):
    is_approved = all('invalid' not in res for res in state['validation_results'])
    return {'is_approved': is_approved}

graph = StateGraph(ActuatorState)
graph.add_node('validate_torque', validate_torque)
graph.add_node('validate_ip', validate_ip_rating)
graph.add_node('finalize', finalize_check)
graph.set_entry_point('validate_torque')
graph.add_edge('validate_torque', 'validate_ip')
graph.add_edge('validate_ip', 'finalize')
graph.add_edge('finalize', END)
actuator_graph = graph.compile()