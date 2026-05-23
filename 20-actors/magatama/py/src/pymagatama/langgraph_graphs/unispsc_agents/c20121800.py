from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    part_id: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_specs(state: ActuatorState):
    log = []
    if state['specs'].get('load_capacity_kg', 0) <= 0:
        log.append('Invalid load capacity')
    return {'validation_log': log}

def assembly_check(state: ActuatorState):
    return {'status': 'validated' if not state['validation_log'] else 'rejected'}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assembly_check)
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
