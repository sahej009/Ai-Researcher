import os
import time
import statistics
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import cohere

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# 1. Corpus with subtle semantic distractors where dense embeddings alone struggle
CORPUS = [
    {"id": 1, "text": "Project Kronos: The production PostgreSQL database max_connections limit is strictly set to 250 connections per node, managed via PgBouncer pooling."},
    {"id": 2, "text": "Project Kronos staging environment uses a default max_connections setting of 100 for local developer testing and integration runs."},
    {"id": 3, "text": "Database administration policy recommends monitoring PostgreSQL connection utilization and pool saturation via Prometheus exporters."},
    {"id": 4, "text": "Enterprise Refunds SLA: Tier-1 enterprise clients receive automated wire refunds within 24 business hours if API uptime drops below 99.95%."},
    {"id": 5, "text": "Standard self-serve subscription refunds are processed within 5 to 7 business days following billing support approval."},
    {"id": 6, "text": "SLA uptime credits are calculated monthly based on total minutes of gateway unscheduled downtime."},
    {"id": 7, "text": "Zero-Trust MCP Adapter: All incoming tool payloads must pass Microsoft Presidio PII scrubbing before context injection into Llama-3.3-70b."},
    {"id": 8, "text": "Llama-3.3-70b context windows support up to 128k tokens for multi-agent synthesis in CrewAI research workflows."},
    {"id": 9, "text": "Authentication tokens use HS256 JWT signing with a strict 60-minute expiration window and tenant_id claims."},
    {"id": 10, "text": "Legacy OAuth2 refresh tokens expire after 14 days of inactivity across mobile client sessions."},
    {"id": 11, "text": "Qdrant vector collections use Cosine distance with HNSW indexing (m=16, ef_construct=100) over 384-dimensional Hugging Face embeddings."},
    {"id": 12, "text": "Vector search chunking splits enterprise PDFs into 512-token chunks with a 64-token overlap using LlamaIndex SentenceSplitter."},
    {"id": 13, "text": "Rate limiting policy: Free-tier tenants are throttled at 30 requests per minute, whereas Enterprise tenants burst up to 500 RPS via Redis token buckets."},
    {"id": 14, "text": "Redis semantic cache stores query embeddings with a 0.92 cosine similarity threshold and a 24-hour TTL."},
    {"id": 15, "text": "Disaster Recovery RTO: Active-passive cross-region failover to AWS ap-south-1 completes within 15 minutes with an RPO of under 60 seconds."},
    {"id": 16, "text": "Nightly cold database backups are snapshotted to AWS S3 Glacier every 24 hours for 7-year compliance retention."},
]

EVAL_QUERIES = [
    {"query": "What is the max_connections limit for Project Kronos in production?", "expected_id": 1},
    {"query": "How fast are refunds processed for Tier-1 enterprise clients when uptime breaches SLA?", "expected_id": 4},
    {"query": "What PII security step happens before payloads reach Llama-3.3-70b in the MCP adapter?", "expected_id": 7},
    {"query": "When do HS256 JWT authentication tokens expire?", "expected_id": 9},
    {"query": "What HNSW parameters and distance metric are configured on the Qdrant collection?", "expected_id": 11},
    {"query": "What chunk size and overlap are used by LlamaIndex for enterprise PDFs?", "expected_id": 12},
    {"query": "What is the burst rate limit in RPS for Enterprise tenants?", "expected_id": 13},
    {"query": "What cosine similarity threshold is used by the Redis semantic cache?", "expected_id": 14},
    {"query": "What is the Recovery Time Objective (RTO) for cross-region failover to ap-south-1?", "expected_id": 15},
]


def calc_mrr(ranked_ids: list[int], expected_id: int) -> float:
    for rank, doc_id in enumerate(ranked_ids, start=1):
        if doc_id == expected_id:
            return 1.0 / rank
    return 0.0


def run_benchmark():
    print("Loading HuggingFace Embedding Model...")
    embedder = SentenceTransformer(EMBED_MODEL_NAME)
    qdrant = QdrantClient(":memory:")
    collection_name = "enterprise_rag_bench"

    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    # Measure indexing throughput
    t0 = time.perf_counter()
    vectors = embedder.encode([doc["text"] for doc in CORPUS])
    points = [
        PointStruct(id=doc["id"], vector=vec.tolist(), payload=doc)
        for doc, vec in zip(CORPUS, vectors)
    ]
    qdrant.upsert(collection_name=collection_name, points=points)
    ingest_ms = (time.perf_counter() - t0) * 1000

    co = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None

    qdrant_latencies = []
    rerank_latencies = []
    base_mrr_scores, rerank_mrr_scores = [], []
    base_hits_top1, rerank_hits_top1 = 0, 0
    base_hits_top3, rerank_hits_top3 = 0, 0

    for item in EVAL_QUERIES:
        q_start = time.perf_counter()
        q_vec = embedder.encode(item["query"]).tolist()
        hits = qdrant.query_points(
            collection_name=collection_name,
            query=q_vec,
            limit=10,
        ).points
        qdrant_latencies.append((time.perf_counter() - q_start) * 1000)

        base_top3_ids = [h.id for h in hits[:3]]
        base_mrr_scores.append(calc_mrr(base_top3_ids, item["expected_id"]))
        if base_top3_ids[0] == item["expected_id"]:
            base_hits_top1 += 1
        if item["expected_id"] in base_top3_ids:
            base_hits_top3 += 1

        if co:
            r_start = time.perf_counter()
            docs = [h.payload["text"] for h in hits]
            reranked = co.rerank(
                model="rerank-english-v3.0",
                query=item["query"],
                documents=docs,
                top_n=3,
            )
            rerank_latencies.append((time.perf_counter() - r_start) * 1000)
            rerank_top3_ids = [hits[r.index].id for r in reranked.results]
        else:
            rerank_top3_ids = base_top3_ids

        rerank_mrr_scores.append(calc_mrr(rerank_top3_ids, item["expected_id"]))
        if rerank_top3_ids[0] == item["expected_id"]:
            rerank_hits_top1 += 1
        if item["expected_id"] in rerank_top3_ids:
            rerank_hits_top3 += 1

    n = len(EVAL_QUERIES)
    print("\n================ RAG BENCHMARK RESULTS ================")
    print(f"Indexed Chunks:              {len(CORPUS)} chunks in {ingest_ms:.1f} ms")
    print(f"Median Qdrant Search Latency: {statistics.median(qdrant_latencies):.2f} ms (p95: {max(qdrant_latencies):.2f} ms)")
    print(f"Base Qdrant Top-1 Accuracy:   {(base_hits_top1 / n) * 100:.1f}%")
    print(f"Base Qdrant Top-3 Hit Rate:   {(base_hits_top3 / n) * 100:.1f}%")
    print(f"Base Qdrant MRR@3:            {statistics.mean(base_mrr_scores):.3f}")
    if co:
        print("-------------------------------------------------------")
        print(f"Cohere Rerank Top-1 Accuracy: {(rerank_hits_top1 / n) * 100:.1f}%")
        print(f"Cohere Rerank Top-3 Hit Rate: {(rerank_hits_top3 / n) * 100:.1f}%")
        print(f"Cohere Rerank MRR@3:          {statistics.mean(rerank_mrr_scores):.3f}")
        print(f"Median Rerank API Latency:    {statistics.median(rerank_latencies):.2f} ms")
    else:
        print("\n[Note] COHERE_API_KEY not found in .env - skipped live Cohere API call.")
    print("=======================================================")


if __name__ == "__main__":
    run_benchmark()