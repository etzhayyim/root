from langgraph.graph import StateGraph, END
from typing import TypedDict
class MailboxState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_log: list
def validate_specs(state: MailboxState):
    required = ['Material Grade', 'Locking Mechanism Type']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_status': len(missing) == 0, 'error_log': missing}
def check_compliance(state: MailboxState):
    return {'validation_status': True if state['spec_data'].get('Regulatory Compliance') else False}
graph = StateGraph(MailboxState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()