from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BoltSpecState(TypedDict):
    material_grade: str
    tensile_strength: float
    status: str
    validation_log: List[str]

def validate_physics(state: BoltSpecState):
    log = state.get('validation_log', [])
    if state['tensile_strength'] < 800:
        status = 'REJECTED'
        log.append('Tensile strength below safety threshold')
    else:
        status = 'APPROVED'
        log.append('Tensile strength meets industrial standards')
    return {'status': status, 'validation_log': log}

workflow = StateGraph(BoltSpecState)
workflow.add_node('physics_check', validate_physics)
workflow.set_entry_point('physics_check')
workflow.add_edge('physics_check', END)
graph = workflow.compile()