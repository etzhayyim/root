from langgraph.graph import StateGraph, END
from typing import TypedDict
class WrenchState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list
def validate_specs(state: WrenchState):
    hardness = state['spec_data'].get('hardness_rating_hrc', 0)
    is_valid = 40 <= hardness <= 55
    return {'validation_result': is_valid, 'error_log': [] if is_valid else ['Hardness out of standard range']}
def compile_graph():
    graph = StateGraph(WrenchState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()
graph = compile_graph()
