from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrassIngotState(TypedDict):
    purity_level: float
    alloy_composition: dict
    compliance_report: str

def validate_composition(state: BrassIngotState):
    if state['alloy_composition'].get('copper', 0) < 55.0:
        return {'compliance_report': 'FAILED: Insufficient copper content'}
    return {'compliance_report': 'PASSED: Within industry standards'}

def process_ingot(state: BrassIngotState):
    print(f'Processing batch with status: {state['compliance_report']}')
    return {'compliance_report': 'PROCESSED'}

graph = StateGraph(BrassIngotState)
graph.add_node('validator', validate_composition)
graph.add_node('processor', process_ingot)
graph.add_edge('validator', 'processor')
graph.add_edge('processor', END)
graph.set_entry_point('validator')
graph = graph.compile()