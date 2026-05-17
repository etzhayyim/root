from typing import TypedDict
from langgraph.graph import StateGraph, END

class RetainerState(TypedDict):
    order_id: str
    cad_file_path: str
    is_validated: bool
    compliance_report: str

def validate_cad_files(state: RetainerState):
    print(f'Validating CAD file for {state[\'order_id\']}')
    return {'is_validated': True}

def generate_compliance(state: RetainerState):
    return {'compliance_report': 'Compliant with ISO 10993'}

graph = StateGraph(RetainerState)
graph.add_node('validate', validate_cad_files)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()