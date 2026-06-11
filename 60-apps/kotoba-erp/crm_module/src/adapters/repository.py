from kotoba_langgraph import _cbor as cbor2
from typing import Optional
from datetime import datetime
from src.domain.entities import Account, Contact, Opportunity

try:
    from wit_world import kqe, kse
    from wit_world.types import Quad
except ImportError:
    class Quad:
        def __init__(self, graph: str, subject: str, predicate: str, object_cbor: bytes):
            self.graph = graph
            self.subject = subject
            self.predicate = predicate
            self.object_cbor = object_cbor
            
    class _KqeMock:
        def assert_quad(self, q: Quad) -> None: pass
        def get_objects(self, graph: str, subject: str, predicate: str) -> list[bytes]:
            if predicate == "sfdc:opportunity":
                return [cbor2.dumps({
                    "Id": "006000000000001AAA",
                    "AccountId": "001000000000001AAA",
                    "Name": "Big Deal 2026",
                    "StageName": "Negotiation/Review",
                    "Amount": 50000.0,
                    "CloseDate": datetime.now().isoformat(),
                    "Probability": 90.0
                })]
            return []
        
    class _KseMock:
        def publish(self, topic: str, payload: bytes) -> str: return "mock-cid"

    kqe = _KqeMock()
    kse = _KseMock()

class CRMRepository:
    def __init__(self, graph_name: str = "crm_salesforce"):
        self.graph_name = graph_name

    def get_opportunity(self, opp_id: str) -> Optional[Opportunity]:
        """Fetch Salesforce Opportunity from KQE using true read API."""
        subject = f"Opportunity:{opp_id}"
        
        objs = kqe.get_objects(self.graph_name, subject, "sfdc:opportunity")
        if not objs:
            return None
            
        data = cbor2.loads(bytes(objs[0]))
        
        return Opportunity(
            Id=data["Id"],
            AccountId=data["AccountId"],
            Name=data["Name"],
            StageName=data["StageName"],
            Amount=data["Amount"],
            CloseDate=datetime.fromisoformat(data["CloseDate"]),
            Probability=data["Probability"]
        )

    def save_opportunity(self, opp: Opportunity) -> None:
        """Persist Opportunity to Kotoba KQE and publish to KSE if Won."""
        subject = f"Opportunity:{opp.Id}"
        
        data = {
            "Id": opp.Id,
            "AccountId": opp.AccountId,
            "Name": opp.Name,
            "StageName": opp.StageName,
            "Amount": opp.Amount,
            "CloseDate": opp.CloseDate.isoformat(),
            "Probability": opp.Probability
        }
        
        kqe.assert_quad(Quad(
            graph=self.graph_name,
            subject=subject,
            predicate="sfdc:opportunity",
            object_cbor=list(cbor2.dumps(data))
        ))
        
        # Cross-Cloud Integration: Salesforce to SAP
        # Publish an event to the stream engine for the SD module to pick up
        if opp.StageName == 'Closed Won':
            event_payload = {
                "event_type": "OpportunityClosedWon",
                "opportunity_id": opp.Id,
                "account_id": opp.AccountId,
                "amount": opp.Amount,
                "timestamp": datetime.now().isoformat()
            }
            kse.publish("crm.opportunity.won", list(cbor2.dumps(event_payload)))
