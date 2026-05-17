from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotArmState(TypedDict):
    part_id: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: RobotArmState):
    log = []
    # Simulate CAD/Tolerance validation logic
    if 'tolerance' in state['specs'] and state['specs']['tolerance'] < 0.005:
        log.append('Tolerance meets high-precision requirement.')
    else:
        log.append('Tolerance check failed.')
    return {'validation_log': log}

def approval_check(state: RobotArmState):
    is_approved = 'Tolerance meets high-precision requirement.' in state['validation_log']
    return {'is_approved': is_approved}

graph = StateGraph(RobotArmState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()