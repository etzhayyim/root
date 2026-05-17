from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GearState(TypedDict):
    gear_specs: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: GearState):
    specs = state['gear_specs']
    logs = []
    if specs.get('hardness_hrc', 0) < 55:
        logs.append('Insufficient hardness for mining application')
    return {'validation_logs': logs, 'is_approved': len(logs) == 0}

def prepare_logistics(state: GearState):
    return {'validation_logs': ['Logistics procurement initiated for high-value steel gear']}

graph = StateGraph(GearState)
graph.add_node('validate', validate_specs)
graph.add_node('logistics', prepare_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()