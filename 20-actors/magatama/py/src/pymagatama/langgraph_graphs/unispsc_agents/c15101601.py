from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class HeavyMachineryState(TypedDict):
    machinery_id: str
    spec_sheet: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: HeavyMachineryState):
    log = ['Specs received for ' + state['machinery_id']]
    compliant = state['spec_sheet'].get('load_capacity', 0) > 0
    return {'validation_log': log, 'is_compliant': compliant}

def route_by_compliance(state: HeavyMachineryState):
    return 'compliant' if state['is_compliant'] else 'flag_for_review'

graph = StateGraph(HeavyMachineryState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()