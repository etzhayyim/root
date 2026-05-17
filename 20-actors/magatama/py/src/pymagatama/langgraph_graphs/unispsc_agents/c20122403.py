from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class LinearBearingState(TypedDict):
    part_number: str
    spec_requirements: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_bearing_specs(state: LinearBearingState):
    specs = state['spec_requirements']
    logs = []
    compliant = True
    if specs.get('iso_precision_grade', 0) < 5:
        logs.append('Validation Error: Precision grade below required threshold.')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def update_robotics_inventory(state: LinearBearingState):
    if state['is_compliant']:
        return {'validation_logs': ['Inventory updated successfully.']}
    return {'validation_logs': ['Inventory update blocked due to non-compliance.']}

graph = StateGraph(LinearBearingState)
graph.add_node('validate', validate_bearing_specs)
graph.add_node('inventory', update_robotics_inventory)
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()