from typing import TypedDict
from langgraph.graph import StateGraph, END
class EMLAState(TypedDict):
    batch_id: str
    temperature_logs: list[float]
    is_expired: bool
def validate_cold_chain(state: EMLAState):
    temp_valid = all(2 <= t <= 8 for t in state['temperature_logs'])
    print(f'Cold chain valid: {temp_valid}')
    return {'is_expired': False}
def verify_regulatory(state: EMLAState):
    print(f'Validating batch: {state['batch_id']}')
    return {'is_expired': False}
graph = StateGraph(EMLAState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('regulatory', verify_regulatory)
graph.set_entry_point('cold_chain')
graph.add_edge('cold_chain', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()