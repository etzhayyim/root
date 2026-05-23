from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class RobotAxisState(TypedDict):
    part_id: str
    specs: dict
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_specs(state: RobotAxisState) -> RobotAxisState:
    torque = state['specs'].get('torque_rating', 0)
    if torque > 500:
        return {'validation_log': ['Torque exceeds safety threshold, triggering manual engineering review.'], 'is_approved': False}
    return {'validation_log': ['Technical specs validated successfully.'], 'is_approved': True}

def process_procurement(state: RobotAxisState) -> RobotAxisState:
    if state['is_approved']:
        return {'validation_log': ['Procurement workflow initiated for qualified component.']}
    return {'validation_log': ['Component failed validation, order halted.']}

graph = StateGraph(RobotAxisState)
graph.add_node('validate', validate_specs)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()
