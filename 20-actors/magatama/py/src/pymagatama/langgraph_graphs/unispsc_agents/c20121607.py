from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_sheet: dict
    validation_log: List[str]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    log = []
    if state['spec_sheet'].get('torque_rating_nm', 0) <= 0:
        log.append('Invalid torque rating')
    return {'validation_log': log, 'is_compliant': len(log) == 0}

def compile_graph():
    workflow = StateGraph(ActuatorState)
    workflow.add_node('validate', validate_specs)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', END)
    return workflow.compile()

graph = compile_graph()
