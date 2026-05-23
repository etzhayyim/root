from typing import TypedDict
from langgraph.graph import StateGraph, END

class LenograstimState(TypedDict):
    temperature_log: list
    expiry_check: bool
    compliance_validated: bool

def validate_cold_chain(state: LenograstimState):
    # Simulate cold chain validation logic
    temp_ok = all(t <= 8.0 for t in state['temperature_log'])
    print(f'Temperature criteria met: {temp_ok}')
    return {'compliance_validated': temp_ok}

def verify_regulatory_docs(state: LenograstimState):
    # Simulate GMP and batch documentation check
    return {'expiry_check': True}

graph = StateGraph(LenograstimState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('regulatory', verify_regulatory_docs)
graph.set_entry_point('cold_chain')
graph.add_edge('cold_chain', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
