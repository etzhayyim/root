from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    commodity_code: str
    gsm: float
    recycled_content: float
    is_compliant: bool

def validate_paper_spec(state: PaperProcurementState):
    is_compliant = state['gsm'] >= 60 and state['recycled_content'] >= 30
    return {'is_compliant': is_compliant}

def process_procurement(state: PaperProcurementState):
    print(f'Processing procurement for {state['commodity_code']}')
    return {}

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_paper_spec)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()