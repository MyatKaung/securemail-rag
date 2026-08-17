from securemail.retrieval.bm25 import BM25Retriever
from securemail.retrieval.documents import RetrievalDocument
from securemail.security import (
    DEMO_IDENTITIES,
    AuthorizationFilter,
    SyntheticRBACPolicy,
    UnknownDemoIdentityError,
    resolve_demo_identity,
)


def document(email_id: str, department: str, scope: str) -> RetrievalDocument:
    return RetrievalDocument(
        email_id=email_id,
        text=f"Subject: {email_id}\nBody: evidence",
        metadata={
            "department": department,
            "access_level": (
                "global" if scope == "global" else "standard" if scope == "shared" else "department"
            ),
            "resource_scope": scope,
        },
    )


def test_server_resolver_returns_only_trusted_principals() -> None:
    assert resolve_demo_identity("FINANCE@SECUREMAIL.DEMO").department == "finance"
    assert resolve_demo_identity("admin@securemail.demo").role == "admin"
    assert set(DEMO_IDENTITIES) == {
        "finance@securemail.demo",
        "legal@securemail.demo",
        "employee@securemail.demo",
        "admin@securemail.demo",
    }


def test_unknown_identity_is_rejected() -> None:
    try:
        resolve_demo_identity("attacker@securemail.demo")
    except UnknownDemoIdentityError:
        pass
    else:
        raise AssertionError("unknown identity was accepted")


def test_existing_policy_keeps_department_shared_and_admin_boundaries() -> None:
    documents = [
        document("finance-email", "finance", "finance"),
        document("shared-email", "general", "shared"),
        document("legal-email", "legal", "legal"),
        document("global-email", "global", "global"),
    ]
    policy = SyntheticRBACPolicy()

    finance = AuthorizationFilter(resolve_demo_identity("finance@securemail.demo"), policy)
    legal = AuthorizationFilter(resolve_demo_identity("legal@securemail.demo"), policy)
    shared = AuthorizationFilter(resolve_demo_identity("employee@securemail.demo"), policy)
    admin = AuthorizationFilter(resolve_demo_identity("admin@securemail.demo"), policy)

    def retrieved_ids(authorization_filter: AuthorizationFilter) -> list[str]:
        retriever = BM25Retriever(
            documents,
            top_k=len(documents),
            authorization_filter=authorization_filter,
        )
        return [item.email_id for item in retriever.retrieve("evidence", top_k=len(documents))]

    assert retrieved_ids(finance) == ["finance-email"]
    assert retrieved_ids(legal) == ["legal-email"]
    assert retrieved_ids(shared) == ["shared-email"]
    assert set(retrieved_ids(admin)) == {
        "finance-email",
        "shared-email",
        "legal-email",
        "global-email",
    }
