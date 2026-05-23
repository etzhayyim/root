from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PropofolState(TypedDict):
    batch_number: str
    temperature_logs: List[float]
    is_compliant: bool

def validate_cold_chain(state: PropofolState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs'])
    return {'is_compliant': 2 <= avg_temp <= 8}

workflow = StateGraph(PropofolState)
workflow.add_node('cold_chain_check', validate_cold_chain)
workflow.set_entry_point('cold_chain_check')
workflow.add_edge('cold_chain_check', END)
graph = workflow.compile()
