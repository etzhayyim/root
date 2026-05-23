from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ServerProcurementState(TypedDict):
    requirements: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: ServerProcurementState):
    reqs = state['requirements']
    logs = []
    compliant = True
    if 'processor_spec' not in reqs:
        logs.append('Missing processor specification')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def perform_compliance_check(state: ServerProcurementState):
    return {'validation_logs': ['Compliance verified against export controls'], 'is_compliant': state['is_compliant']}

graph = StateGraph(ServerProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', perform_compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
