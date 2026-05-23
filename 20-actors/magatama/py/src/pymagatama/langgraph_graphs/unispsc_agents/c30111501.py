from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ConcreteState(TypedDict):
    density: float
    strength: float
    is_compliant: bool

def validate_density(state: ConcreteState):
    state['is_compliant'] = state['density'] >= 400 and state['density'] <= 1600
    return state

workflow = StateGraph(ConcreteState)
workflow.add_node('density_check', validate_density)
workflow.set_entry_point('density_check')
workflow.add_edge('density_check', END)
graph = workflow.compile()
