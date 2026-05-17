from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temperature_logs: list[float]
    is_validated: bool

def validate_cold_chain(state: VaccineState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs'])
    validated = 2.0 <= avg_temp <= 8.0
    return {'is_validated': validated}

def process_vaccine(state: VaccineState):
    print(f'Processing Batch: {state['batch_id']}')
    return {}

graph = StateGraph(VaccineState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('process', process_vaccine)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()