from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ActuatorState(TypedDict):
    specs: dict
    validation_results: Annotated[list[str], operator.add]
    is_approved: bool

def validate_mechanical_specs(state: ActuatorState):
    specs = state.get(specs, {})
    results = []
    if specs.get(positioning_accuracy_micron, 1000) > 50:
        results.append(High precision requirement failed)
    return {validation_results: results}

def check_compliance(state: ActuatorState):
    is_compliant = len(state.get(validation_results, [])) == 0
    return {is_approved: is_compliant}

builder = StateGraph(ActuatorState)
builder.add_node(validate, validate_mechanical_specs)
builder.add_node(compliance, check_compliance)
builder.add_edge(validate, compliance)
builder.add_edge(compliance, END)
builder.set_entry_point(validate)
graph = builder.compile()