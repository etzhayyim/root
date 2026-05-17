from typing import TypedDict
from langgraph.graph import StateGraph, END

class PeriodontalState(TypedDict):
    item_id: str
    compliance_cleared: bool
    sterilization_validated: bool

def check_regulatory(state: PeriodontalState):
    print(f'Checking {state["item_id"]} regulatory filing...')
    return {'compliance_cleared': True}

def validate_sterilization(state: PeriodontalState):
    print(f'Validating sterilization protocols for {state["item_id"]}...')
    return {'sterilization_validated': True}

graph = StateGraph(PeriodontalState)
graph.add_node('regulatory', check_regulatory)
graph.add_node('sterilization', validate_sterilization)
graph.set_entry_point('regulatory')
graph.add_edge('regulatory', 'sterilization')
graph.add_edge('sterilization', END)
graph = graph.compile()