from typing import TypedDict
from langgraph.graph import StateGraph, END

class MailboxPowerState(TypedDict):
    model_id: str
    voltage_spec: str
    is_compatible: bool
    approved: bool

def validate_specs(state: MailboxPowerState):
    # Simple logic for power compatibility check
    required_voltage = 220
    state['is_compatible'] = int(state['voltage_spec']) >= required_voltage
    return {'is_compatible': state['is_compatible']}

def approval_step(state: MailboxPowerState):
    state['approved'] = state['is_compatible']
    return {'approved': state['approved']}

graph = StateGraph(MailboxPowerState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()