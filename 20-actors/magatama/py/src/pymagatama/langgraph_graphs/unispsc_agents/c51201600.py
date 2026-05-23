from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temperature_logs: list
    gmp_status: bool
    is_compliant: bool

def validate_cold_chain(state: VaccineState):
    compliant = all(temp <= 8.0 for temp in state['temperature_logs'])
    print(f'Validating storage for {state['batch_id']}')
    return {'is_compliant': compliant}

def check_compliance(state: VaccineState):
    return 'compliant' if state['is_compliant'] and state['gmp_status'] else 'non_compliant'

graph = StateGraph(VaccineState)
graph.add_node('validate', validate_cold_chain)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
