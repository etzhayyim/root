from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    servo_id: str
    torque_nm: float
    status: str

def validate_specs(state: ServoState) -> ServoState:
    if state['torque_nm'] < 0:
        state['status'] = 'INVALID_TORQUE'
    else:
        state['status'] = 'VALIDATED'
    return state

def check_compliance(state: ServoState) -> ServoState:
    if state['status'] == 'VALIDATED':
        state['status'] = 'COMPLIANT'
    return state

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()