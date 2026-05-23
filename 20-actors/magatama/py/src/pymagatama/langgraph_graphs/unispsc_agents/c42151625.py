from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalToolState(TypedDict):
    tool_id: str
    compliance_docs: list
    is_sterile_ready: bool

def validate_certification(state: DentalToolState):
    print(f'Validating ISO 13485 for {state["tool_id"]}')
    return {'is_sterile_ready': True}

def process_procurement(state: DentalToolState):
    print(f'Processing procurement workflow for dental instrument {state["tool_id"]}')
    return {'compliance_docs': ['ISO-13485-Cert']}

graph = StateGraph(DentalToolState)
graph.add_node('validate', validate_certification)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
