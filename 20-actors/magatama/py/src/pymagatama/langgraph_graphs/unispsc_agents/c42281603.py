from typing import TypedDict
from langgraph.graph import StateGraph, END

class DisinfectantState(TypedDict):
    product_specs: dict
    compliance_ok: bool
    approved: bool

def validate_concentration(state: DisinfectantState):
    conc = state['product_specs'].get('concentration', 0)
    return {'compliance_ok': conc > 0}

def check_regulatory(state: DisinfectantState):
    return {'approved': state.get('compliance_ok', False)}

graph = StateGraph(DisinfectantState)
graph.add_node('validate', validate_concentration)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)

app = graph.compile()