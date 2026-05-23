from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    requirements: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: ServoState):
    req = state['requirements']
    logs = []
    if req.get('torque', 0) <= 0:
        logs.append('Invalid torque specification')
    return {'validation_log': logs}

def check_compliance(state: ServoState):
    compliant = len(state['validation_log']) == 0
    return {'is_compliant': compliant}

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
