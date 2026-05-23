from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_refractory_specs(state: State):
    reqs = {'max_abrasion_loss': 5.0, 'min_alumina_pct': 40.0}
    specs = state['spec_data']
    valid = specs.get('abrasion_loss', 10) <= reqs['max_abrasion_loss'] and specs.get('alumina_pct', 0) >= reqs['min_alumina_pct']
    return {'validation_result': valid}

graph = StateGraph(State)
graph.add_node('validate', validate_refractory_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
