from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SolventState(TypedDict):
    flash_point: float
    has_sds: bool
    compliant: bool
    risk_assessment: str

def validate_solvent(state: SolventState):
    compliant = state['has_sds'] and state['flash_point'] > 0
    return {'compliant': compliant, 'risk_assessment': 'High' if state['flash_point'] < 60 else 'Standard'}

graph = StateGraph(SolventState)
graph.add_node('validate', validate_solvent)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
