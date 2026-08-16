# SecureMail RAG — Architecture

## High-Level Architecture

```text
                         User
                          |
                          v
                  FastAPI / Simple UI
                          |
                          v
                      LangGraph
                          |
                    Query Analysis
                          |
          +---------------+----------------+
          |                                |
          v                                v
   Knowledge / RAG                 Optional Analytics
          |                                |
          v                                v
 Authorization Context                Text2SQL
          |                                |
          v                                v
 PRE-RETRIEVAL FILTER                 PostgreSQL
          |
    +-----+------+
    |            |
    v            v
   BM25        Dense
    |            |
    +-----+------+
          |
      RRF / Fusion
          |
       Reranker
          |
 Authorized Top-K Evidence
          |
  Optional CRAG / Self-RAG
          |
          v
 Qwen3.6-27B via OpenRouter
          |
          v
 Answer + citations/source IDs
```

## Security Boundary
Authorization must be applied before candidate retrieval.

Bad:
```text
search all -> retrieve restricted email -> remove later
```

Required:
```text
user identity -> authorization filter -> search authorized corpus
```

## Primary Components

### Ingestion
Responsibilities:
- parse Enron emails
- normalize sender/recipient/date/subject/body/mailbox
- deduplicate
- create stable email IDs
- attach synthetic authorization metadata
- write structured metadata
- prepare text for indexing

### Retrieval
Common interface supports:
- `BM25Retriever`
- `DenseRetriever`
- `HybridRetriever`

Authorization must be injected into the common retrieval path.

### Reranking
Input: larger candidate set, e.g. top 20.
Output: smaller evidence set, e.g. top 5.

### Generation
OpenRouter model:
`qwen/qwen3.6-27b`

Must:
- answer from provided evidence
- cite source IDs
- state insufficient evidence instead of inventing facts

### Optional Text2SQL
Use only for structured email metadata questions such as:
- counts by sender
- date-range counts
- sender/recipient interaction counts

Text2SQL is not part of P0.

## Data Stores
MVP may use:
- vector index chosen by implementation
- BM25 index
- PostgreSQL or SQLite for structured metadata/eval/feedback where appropriate

Keep store access behind interfaces so storage can be changed without rewriting business logic.

## Configuration
- `.env`: secrets only
- `config/models.yaml`: model/provider settings
- `config/app.yaml`: non-secret application settings

## Cloud
Architecture must be containerized and cloud-ready, but public deployment is P3.
