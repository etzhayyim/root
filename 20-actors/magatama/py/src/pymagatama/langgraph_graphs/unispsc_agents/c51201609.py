from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temp_log: list[float]
    is_compliant: bool

def validate_cold_chain(state: VaccineState):
    avg_temp = sum(state['temp_log']) / len(state['temp_log']) if state['temp_log'] else 10.0
    return {'is_compliant': 2.0 <= avg_temp <= 8.0}

def process_vaccine_data(state: VaccineState):
    print(f'Processing batch {state['batch_id']}. Compliance status: {state['is_compliant']}')
    return state

graph = StateGraph(VaccineState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('process', process_vaccine_data)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
compile_graph = graph.compile()