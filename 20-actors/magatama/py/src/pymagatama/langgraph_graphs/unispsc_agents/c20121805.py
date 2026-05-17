from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class LubricantState(TypedDict):
    commodity_id: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_viscosity(state: LubricantState):
    log = []
    if state['specs'].get('viscosity_index', 0) < 100:
        log.append('Low viscosity index detected for industrial standard')
    return {'validation_log': log}

def check_compliance(state: LubricantState):
    is_compliant = 'Low viscosity index detected' not in ' '.join(state['validation_log'])
    return {'is_compliant': is_compliant}

graph = StateGraph(LubricantState)
graph.add_node('validate_viscosity', validate_viscosity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_viscosity')
graph.add_edge('validate_viscosity', 'check_compliance')
graph.add_edge('check_compliance', END)

# Compile the graph
app = graph.compile()