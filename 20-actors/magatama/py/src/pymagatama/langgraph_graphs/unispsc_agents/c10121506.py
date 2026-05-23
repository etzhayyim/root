from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class FertilizerState(TypedDict):
    input_data: dict
    analysis_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_composition(state: FertilizerState):
    input_data = state['input_data']
    results = []
    compliant = True
    if input_data.get('heavy_metals', 0) > 0.05:
        results.append('High heavy metal content')
        compliant = False
    return {'analysis_results': results, 'is_compliant': compliant}

def route_by_compliance(state: FertilizerState):
    return 'process' if state['is_compliant'] else END

def process_fertilizer_order(state: FertilizerState):
    return {'analysis_results': ['Composition validated and cleared for procurement']}

graph = StateGraph(FertilizerState)
graph.add_node('validate', validate_composition)
graph.add_node('process', process_fertilizer_order)
graph.add_edge('validate', 'process')
graph.add_conditional_edges('validate', route_by_compliance, {'process': 'process', '__end__': END})
graph.set_entry_point('validate')
graph.add_edge('process', END)
compile_graph = graph.compile()
