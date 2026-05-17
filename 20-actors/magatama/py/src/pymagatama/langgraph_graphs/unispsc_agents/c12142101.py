from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class RubberState(TypedDict):
    specs: dict
    validation_log: Annotated[list, operator.add]
    is_approved: bool

def validate_rubber_specs(state: RubberState):
    specs = state['specs']
    logs = []
    if specs.get('tensile_strength_mpa', 0) < 10:
        logs.append('Insufficient tensile strength')
    return {'validation_log': logs, 'is_approved': len(logs) == 0}

def finalize_procurement(state: RubberState):
    return {'validation_log': ['Procurement finalized']}

graph = StateGraph(RubberState)
graph.add_node('validate', validate_rubber_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)

compile_graph = graph.compile()