from typing import TypedDict
from langgraph.graph import StateGraph, END

class AngelicaState(TypedDict):
    batch_id: str
    purity_check: bool
    lab_results: dict
    approved: bool

def validate_quality(state: AngelicaState):
    check = state['lab_results'].get('pesticide_free', False)
    return {'purity_check': check}

def approval_step(state: AngelicaState):
    is_approved = state['purity_check'] and state['lab_results'].get('contaminants') == 0
    return {'approved': is_approved}

graph = StateGraph(AngelicaState)
graph.add_node('validate', validate_quality)
graph.add_node('approval', approval_step)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()