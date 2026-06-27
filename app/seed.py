DEFAULT_KNOWLEDGE_DOCS = [
    {
        "id": "policy-pricing-001",
        "title": "Strategic Account Pricing Policy",
        "source_type": "policy",
        "domain": "B2B SaaS Customer Success",
        "tags": ["pricing", "discount", "renewal", "enterprise"],
        "content": (
            "For strategic enterprise renewals, teams should not lead with a discount. "
            "The recommended first action is an executive value workshop that maps product usage "
            "to business outcomes. Discounts above 10 percent require VP approval and should only "
            "be used after value alignment, churn risk review, and commercial impact analysis."
        ),
    },
    {
        "id": "playbook-renewal-001",
        "title": "Enterprise Renewal Risk Playbook",
        "source_type": "playbook",
        "domain": "B2B SaaS Customer Success",
        "tags": ["renewal", "churn", "customer success", "executive workshop"],
        "content": (
            "When an enterprise customer raises pricing concerns within 90 days of renewal, "
            "the customer success manager should schedule an executive workshop, review adoption "
            "gaps, confirm business value, and create a mutual success plan. If competitors are "
            "mentioned, involve the account executive and product specialist within 48 hours."
        ),
    },
    {
        "id": "support-escalation-001",
        "title": "Support Escalation Guidelines",
        "source_type": "guideline",
        "domain": "B2B SaaS Customer Success",
        "tags": ["support", "escalation", "risk", "sla"],
        "content": (
            "Escalate to premium support when unresolved critical tickets remain open for more "
            "than seven days, when SLA commitments are missed, or when a renewal decision is blocked "
            "by technical instability. Escalation should include an owner, next checkpoint, and "
            "customer-visible resolution plan."
        ),
    },
]


DEFAULT_MEMORY_CASES = [
    {
        "id": "case-spotify-workshop-renewed",
        "customer_name": "Spotify",
        "industry": "Media",
        "segment": "Enterprise",
        "problem": "Pricing concern during renewal with competitor evaluation",
        "recommendation": "Executive value workshop",
        "outcome": "Renewed",
        "confidence": 92,
        "tags": ["pricing", "renewal", "competitor", "workshop"],
        "summary": (
            "Enterprise customer questioned pricing and mentioned competitor evaluation. "
            "A value workshop with executive sponsor helped connect product usage to cost savings. "
            "Customer renewed without discount."
        ),
    },
    {
        "id": "case-freshworks-discount-renewed",
        "customer_name": "Freshworks",
        "industry": "Software",
        "segment": "Mid-Market",
        "problem": "Renewal blocked by budget reduction",
        "recommendation": "Limited renewal discount",
        "outcome": "Renewed",
        "confidence": 78,
        "tags": ["pricing", "discount", "budget", "renewal"],
        "summary": (
            "Customer had confirmed budget reduction and strong adoption. A limited 8 percent "
            "discount with a 12-month expansion checkpoint preserved the renewal."
        ),
    },
    {
        "id": "case-acme-support-churned",
        "customer_name": "Acme Logistics",
        "industry": "Logistics",
        "segment": "Enterprise",
        "problem": "Multiple unresolved support issues before renewal",
        "recommendation": "Standard account follow-up",
        "outcome": "Churned",
        "confidence": 63,
        "tags": ["support", "renewal", "churn", "escalation"],
        "summary": (
            "Customer had repeated unresolved support escalations. The team did not create a "
            "customer-visible recovery plan. Customer churned at renewal."
        ),
    },
    {
        "id": "case-nova-workshop-expanded",
        "customer_name": "Nova Analytics",
        "industry": "Analytics",
        "segment": "Enterprise",
        "problem": "Pricing complaint but strong usage across three teams",
        "recommendation": "Executive value workshop",
        "outcome": "Expanded",
        "confidence": 90,
        "tags": ["pricing", "usage", "expansion", "workshop"],
        "summary": (
            "Customer complained about pricing but usage data showed strong adoption. "
            "The executive workshop reframed the conversation around ROI and uncovered expansion potential."
        ),
    },
]