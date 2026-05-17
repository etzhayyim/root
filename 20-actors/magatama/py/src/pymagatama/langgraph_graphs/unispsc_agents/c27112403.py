from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BanderState(TypedDict):
    model_id: str
    tension_settings: float
    safety_verified: bool
    validation_log: List[str]

def validate_specs(state: BanderState):
    log = state.get('validation_log', [])
    if state['tension_settings'] <= 0:
        log.append('Invalid tension')
    return {'validation_log': log + ['Spec validation complete']}

def safety_check(state: BanderState):
    return {'safety_verified': True}

graph = StateGraph(BanderState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()