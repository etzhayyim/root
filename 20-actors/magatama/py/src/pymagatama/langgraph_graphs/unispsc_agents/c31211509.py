from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrimerState(TypedDict):
    voc_content: float
    flash_point: float
    compliance_ok: bool

def validate_chemistry(state: PrimerState):
    if state['voc_content'] > 250:
        state['compliance_ok'] = False
    return state

def validate_safety(state: PrimerState):
    if state['flash_point'] < 30:
        state['compliance_ok'] = False
    return state

graph = StateGraph(PrimerState)
graph.add_node('chemistry_check', validate_chemistry)
graph.add_node('safety_check', validate_safety)
graph.set_entry_point('chemistry_check')
graph.add_edge('chemistry_check', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
