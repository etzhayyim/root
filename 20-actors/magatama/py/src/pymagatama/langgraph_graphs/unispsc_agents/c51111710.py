from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EpirubicinState(TypedDict):
    batch_id: str
    temperature_logs: List[float]
    compliance_docs: List[str]
    validation_passed: bool

def validate_cold_chain(state: EpirubicinState):
    state['validation_passed'] = all(2.0 <= t <= 8.0 for t in state['temperature_logs'])
    print(f'Temperature validation: {state['validation_passed']}')
    return 'validate_cold_chain'

def check_compliance(state: EpirubicinState):
    state['validation_passed'] = state['validation_passed'] and len(state['compliance_docs']) > 0
    return 'check_compliance'

graph = StateGraph(EpirubicinState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('cold_chain')
graph.add_edge('cold_chain', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()