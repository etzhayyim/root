from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BloodTestState(TypedDict):
    batch_id: str
    temperature_logs: List[float]
    is_compliant: bool

def validate_cold_chain(state: BloodTestState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs'])
    print(f'Validating cold chain for {state['batch_id']}: avg temp {avg_temp}C')
    state['is_compliant'] = -2.0 <= avg_temp <= 8.0
    return 'compliant' if state['is_compliant'] else 'non_compliant'

def log_batch(state: BloodTestState):
    print(f'Batch {state['batch_id']} logged successfully.')
    return 'end'

graph = StateGraph(BloodTestState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('log', log_batch)
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
