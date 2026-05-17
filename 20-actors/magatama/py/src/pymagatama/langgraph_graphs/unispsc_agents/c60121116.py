from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CraftPaperState(TypedDict):
    specifications: dict
    validation_status: str
    compliance_checks: List[str]

def validate_paper_specs(state: CraftPaperState):
    specs = state['specifications']
    if 'gsm' in specs and specs['gsm'] > 0:
        return {'validation_status': 'COMPLIANT', 'compliance_checks': ['gsm_verified']}
    return {'validation_status': 'REJECTED', 'compliance_checks': ['missing_gsm']}

def process_procurement(state: CraftPaperState):
    print(f"Processing procurement: {state['validation_status']}")
    return {}

graph = StateGraph(CraftPaperState)
graph.add_node('validate', validate_paper_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()