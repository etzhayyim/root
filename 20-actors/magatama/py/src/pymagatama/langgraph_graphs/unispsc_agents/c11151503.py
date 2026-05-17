from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ChemicalState(TypedDict):
    purity_level: float
    safety_compliance: bool
    log_entries: Annotated[list[str], operator.add]

def validate_purity(state: ChemicalState):
    if state['purity_level'] < 99.9:
        return {'log_entries': ['Purity level below standard, flagging for review']}
    return {'log_entries': ['Purity verified']}

def check_safety_protocols(state: ChemicalState):
    if not state['safety_compliance']:
        return {'log_entries': ['Safety compliance missing, halting workflow']}
    return {'log_entries': ['Safety protocols validated']}

def build_graph():
    workflow = StateGraph(ChemicalState)
    workflow.add_node('purity_check', validate_purity)
    workflow.add_node('safety_check', check_safety_protocols)
    workflow.set_entry_point('purity_check')
    workflow.add_edge('purity_check', 'safety_check')
    workflow.add_edge('safety_check', END)
    return workflow.compile()

graph = build_graph()