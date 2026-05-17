from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    temp_log: List[float]
    is_compliant: bool

def validate_cold_chain(state: ProcurementState):
    avg_temp = sum(state['temp_log']) / len(state['temp_log']) if state['temp_log'] else 25
    return {'is_compliant': 2.0 <= avg_temp <= 8.0}

def finalize_procurement(state: ProcurementState):
    print(f'Batch {state['batch_id']} compliant status: {state['is_compliant']}')
    return {}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()