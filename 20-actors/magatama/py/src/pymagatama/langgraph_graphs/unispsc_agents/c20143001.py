from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class ShaftState(TypedDict):
    specs: dict
    validation_results: Annotated[list, operator.add]
    is_approved: bool

def validate_specs(state: ShaftState):
    results = []
    if state['specs'].get('hardness') < 50:
        results.append('Hardness failure')
    return {'validation_results': results}

def decision_node(state: ShaftState):
    return 'approved' if not state['validation_results'] else 'manual_review'

graph = StateGraph(ShaftState)
graph.add_node('validate', validate_specs)
graph.add_node('manual_review', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', decision_node, {'approved': END, 'manual_review': 'manual_review'})
graph.add_edge('manual_review', END)
compiled_graph = graph.compile()