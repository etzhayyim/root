from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ActuatorState(TypedDict):
    part_id: str
    specs: dict
    validation_log: List[str]
    status: str

def validate_specs(state: ActuatorState):
    log = []
    if state['specs'].get('resolution', 0) < 0.1:
        log.append('High precision verified')
    else:
        log.append('Standard precision')
    return {'validation_log': log}

def check_compliance(state: ActuatorState):
    log = state['validation_log'] + ['Dual-use compliance checked']
    return {'validation_log': log, 'status': 'READY'}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
