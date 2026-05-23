from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ICState(TypedDict):
    wafer_id: str
    quality_score: float
    export_compliant: bool
    steps: List[str]

def validate_ic_quality(state: ICState):
    # Simulated QA logic for IC
    state['quality_score'] = 0.98
    state['steps'].append('QA_CHECK_PASSED')
    return state

def check_export_compliance(state: ICState):
    # Simulated Export Control logic
    state['export_compliant'] = True
    state['steps'].append('EXPORT_CONTROL_VERIFIED')
    return state

graph = StateGraph(ICState)
graph.add_node('qa', validate_ic_quality)
graph.add_node('export', check_export_compliance)
graph.add_edge('qa', 'export')
graph.add_edge('export', END)
graph.set_entry_point('qa')
graph = graph.compile()
