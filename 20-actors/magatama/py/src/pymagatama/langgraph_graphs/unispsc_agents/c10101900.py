from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AgricomState(TypedDict):
    commodity_id: str
    quality_score: float
    compliance_checks: List[str]
    status: str

def validate_quality(state: AgricomState) -> AgricomState:
    state['quality_score'] = 0.95 if state['commodity_id'] else 0.0
    return state

def check_quarantine(state: AgricomState) -> AgricomState:
    state['compliance_checks'].append('QUARANTINE_CLEARED')
    state['status'] = 'READY'
    return state

workflow = StateGraph(AgricomState)
workflow.add_node('validate', validate_quality)
workflow.add_node('quarantine', check_quarantine)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'quarantine')
workflow.add_edge('quarantine', END)

graph = workflow.compile()
