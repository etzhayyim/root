from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_specs(state: ActuatorState):
    specs = state['spec_data']
    logs = []
    if specs.get('max_pressure_rating_mpa', 0) > 70:
        logs.append('High pressure certification required.')
    return {'validation_log': logs, 'status': 'validated'}

def execute_procurement_workflow(state: ActuatorState):
    return {'status': 'procurement_initiated'}

builder = StateGraph(ActuatorState)
builder.add_node('validate', validate_specs)
builder.add_node('procure', execute_procurement_workflow)
builder.set_entry_point('validate')
builder.add_edge('validate', 'procure')
builder.add_edge('procure', END)
graph = builder.compile()
