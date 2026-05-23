from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class TruckState(TypedDict):
    specs: dict
    validation_results: Annotated[list, operator.add]

def validate_specs(state: TruckState):
    results = []
    if state['specs'].get('gcwr', 0) < 20000:
        results.append('Warning: GCWR below industry standard')
    return {'validation_results': results}

def route_procurement(state: TruckState):
    return 'compliance_check'

graph = StateGraph(TruckState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
