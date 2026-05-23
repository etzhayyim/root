from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ServerProcurementState(TypedDict):
    requirements: List[str]
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_server_specs(state: ServerProcurementState):
    logs = []
    compliant = True
    for req in state['requirements']:
        if 'gb' in req.lower() or 'ghz' in req.lower():
            logs.append(f'Validated performance spec: {req}')
        else:
            compliant = False
            logs.append(f'Failed validation: {req}')
    return {'validation_logs': logs, 'is_compliant': compliant}

def approval_node(state: ServerProcurementState):
    if state['is_compliant']:
        return {'validation_logs': ['Procurement approved.']}
    else:
        return {'validation_logs': ['Procurement rejected for non-compliance.']}

graph = StateGraph(ServerProcurementState)
graph.add_node('validate', validate_server_specs)
graph.add_node('approval', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
