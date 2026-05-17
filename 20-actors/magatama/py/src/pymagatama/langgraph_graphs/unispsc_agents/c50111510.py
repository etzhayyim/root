from typing import TypedDict
from langgraph.graph import StateGraph, END

class MeatProcureState(TypedDict):
    batch_id: str
    temp_log: list
    is_compliant: bool

def validate_cold_chain(state: MeatProcureState):
    state['is_compliant'] = all(t <= 4.0 for t in state['temp_log'])
    print(f'Compliance check: {state['is_compliant']}')
    return 'check_compliance'

def check_compliance(state: MeatProcureState):
    return 'approved' if state['is_compliant'] else 'flag_violation'

graph = StateGraph(MeatProcureState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('approved', lambda x: x)
graph.add_node('flag_violation', lambda x: x)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approved')
graph.add_edge('flag_violation', END)
graph.add_edge('approved', END)
graph = graph.compile()