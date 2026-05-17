from typing import TypedDict
from langgraph.graph import StateGraph, END

class ImplantState(TypedDict):
    serial_number: str
    iso_compliant: bool
    sterilization_verified: bool
    approval_status: str

def validate_certification(state: ImplantState):
    state['iso_compliant'] = True  # Simplified logic
    return 'check_sterilization'

def check_sterilization(state: ImplantState):
    state['sterilization_verified'] = True
    return 'finalize_procurement'

graph = StateGraph(ImplantState)
graph.add_node('cert', validate_certification)
graph.add_node('check_sterilization', check_sterilization)
graph.set_entry_point('cert')
graph.add_edge('cert', 'check_sterilization')
graph.add_edge('check_sterilization', END)
graph = graph.compile()