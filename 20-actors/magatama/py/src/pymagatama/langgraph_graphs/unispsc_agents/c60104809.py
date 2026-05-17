from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class WaveState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[List[str], operator.add]
    status: str

def validate_specs(state: WaveState):
    logs = []
    if 'frequency_range' not in state['spec_data']:
        logs.append('Missing frequency range data')
    return {'validation_logs': logs, 'status': 'validating'}

def approval_step(state: WaveState):
    return {'status': 'approved'}

graph = StateGraph(WaveState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()