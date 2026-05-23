from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiCPowderState(TypedDict):
    purity: float
    particle_size: float
    compliance_checks: List[str]
    status: str

def validate_purity(state: SiCPowderState):
    if state['purity'] >= 99.9:
        return {'status': 'High Purity Validated', 'compliance_checks': state['compliance_checks'] + ['purity_ok']}
    return {'status': 'Failed: Low Purity', 'compliance_checks': state['compliance_checks'] + ['purity_failed']}

def process_material(state: SiCPowderState):
    return {'status': 'Processing for Semiconductor Grade', 'compliance_checks': state['compliance_checks'] + ['processing_started']}

graph = StateGraph(SiCPowderState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('process_material', process_material)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'process_material')
graph.add_edge('process_material', END)

compiled_graph = graph.compile()
