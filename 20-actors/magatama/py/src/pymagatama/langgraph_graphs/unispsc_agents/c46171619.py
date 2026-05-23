from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SecuritySpecState(TypedDict):
    requirements: List[str]
    validation_report: str
    approved: bool

def validate_compliance(state: SecuritySpecState):
    is_compliant = all('ISO' in req or 'FIPS' in req for req in state['requirements'])
    return {'validation_report': 'Compliant' if is_compliant else 'Non-compliant', 'approved': is_compliant}

def security_risk_assessment(state: SecuritySpecState):
    return {'validation_report': state['validation_report'] + ' | Security clearance granted'}

graph = StateGraph(SecuritySpecState)
graph.add_node('Validate', validate_compliance)
graph.add_node('RiskAssess', security_risk_assessment)
graph.add_edge('Validate', 'RiskAssess')
graph.add_edge('RiskAssess', END)
graph.set_entry_point('Validate')
graph = graph.compile()
