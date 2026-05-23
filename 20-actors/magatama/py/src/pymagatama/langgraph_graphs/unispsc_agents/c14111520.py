from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ThermalPaperState(TypedDict):
    spec: dict
    validation_results: List[str]

def validate_paper_spec(state: ThermalPaperState):
    results = []
    if state['spec'].get('paper_weight_gsm', 0) < 50:
        results.append('Weight below standard minimum')
    return {'validation_results': results}

def prepare_logistics(state: ThermalPaperState):
    return {'validation_results': state['validation_results'] + ['Logistics routing finalized']}

graph = StateGraph(ThermalPaperState)
graph.add_node('validate', validate_paper_spec)
graph.add_node('logistics', prepare_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()
