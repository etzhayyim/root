from typing import TypedDict
from langgraph.graph import StateGraph, END

class BreadState(TypedDict):
    temp_log: float
    food_safety_compliant: bool
    status: str

def validate_cold_chain(state: BreadState):
    if state['temp_log'] <= -18.0:
        return {'status': 'Cold chain maintained. Proceeding to safety check.'}
    return {'status': 'Critical failure: Temperature excursion.'}

def check_compliance(state: BreadState):
    compliance = state.get('food_safety_compliant', False)
    return {'status': 'Approved' if compliance else 'Rejected'}

graph = StateGraph(BreadState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()