from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ForensicState(TypedDict):
    incident_id: str
    evidence_hash: str
    extracted_data_path: str
    processing_steps: Annotated[List[str], add_messages]

def initialize_forensic(state: ForensicState):
    return {'processing_steps': [f'Initializing forensic suite for incident {state["incident_id"]}']}

def perform_data_extraction(state: ForensicState):
    return {'processing_steps': [f'Extracting data from {state["extracted_data_path"]}', 'Verifying integrity with hash ' + state['evidence_hash']]}

def secure_vault_audit(state: ForensicState):
    return {'processing_steps': ['Auditing secure vault logs', 'Finalizing evidentiary report']}

graph = StateGraph(ForensicState)
graph.add_node('init', initialize_forensic)
graph.add_node('extract', perform_data_extraction)
graph.add_node('audit', secure_vault_audit)
graph.set_entry_point('init')
graph.add_edge('init', 'extract')
graph.add_edge('extract', 'audit')
graph.add_edge('audit', END)
graph = graph.compile()