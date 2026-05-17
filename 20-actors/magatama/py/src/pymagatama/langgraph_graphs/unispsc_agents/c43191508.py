from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ServerState(TypedDict):
    specs: dict
    validation_logs: Annotated[List[str], add_messages]

def validate_server_specs(state: ServerState):
    specs = state['specs']
    logs = []
    if specs.get('processor_architecture') not in ['x86_64', 'ARM64']:
        logs.append('Invalid processor architecture')
    return {'validation_logs': logs}

def route_by_compliance(state: ServerState):
    if state['validation_logs']:
        return 'error'
    return 'process'

graph = StateGraph(ServerState)
graph.add_node('validate', validate_server_specs)
graph.add_node('process', lambda state: {'validation_logs': ['Success']})
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')