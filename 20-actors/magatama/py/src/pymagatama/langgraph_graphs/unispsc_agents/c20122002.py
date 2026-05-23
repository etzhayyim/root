from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ActuatorState(TypedDict):
    spec_data: dict
    validation_log: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    specs = state['spec_data']
    log = []
    compliant = True
    if specs.get('repeatability_micron', 100) > 50:
        log.append('Precision requirement not met.')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

def compile_graph():
    workflow = StateGraph(ActuatorState)
    workflow.add_node('validate', validate_specs)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', END)
    return workflow.compile()

graph = compile_graph()
