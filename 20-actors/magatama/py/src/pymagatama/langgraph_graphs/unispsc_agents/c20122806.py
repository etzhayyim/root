from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GearState(TypedDict):
    specs: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_gears(state: GearState):
    specs = state['specs']
    logs = []
    approved = True
    if specs.get('backlash_arcmin', 10) > 5:
        logs.append('Warning: High backlash for precision application')
        approved = False
    return {'validation_logs': logs, 'is_approved': approved}

def final_report(state: GearState):
    return {'validation_logs': ['Final check complete: ' + str(state['is_approved'])]}

graph = StateGraph(GearState)
graph.add_node('validate', validate_gears)
graph.add_node('report', final_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()