"""
Initialize Milvus collection for knowledge base vectors.
Run once after Milvus is healthy.
"""
import os
import time
import sys

from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType,
    connections, utility
)

MILVUS_HOST = os.environ.get("MILVUS_HOST", "localhost")
MILVUS_PORT = os.environ.get("MILVUS_PORT", "19530")
COLLECTION_NAME = "knowledge_base_vectors"
DIMENSION = int(os.environ.get("EMBEDDING_DIM", "1536"))

MAX_RETRIES = 30
RETRY_INTERVAL = 2


def connect_with_retry():
    """Connect to Milvus with retry logic."""
    for i in range(MAX_RETRIES):
        try:
            connections.connect(
                alias="default",
                host=MILVUS_HOST,
                port=MILVUS_PORT,
            )
            print(f"Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
            return True
        except Exception as e:
            print(f"Attempt {i+1}/{MAX_RETRIES}: Milvus not ready - {e}")
            time.sleep(RETRY_INTERVAL)
    return False


def init_collection():
    """Create the knowledge_base_vectors collection."""
    if not connect_with_retry():
        print("ERROR: Failed to connect to Milvus after retries")
        sys.exit(1)

    # Drop if exists (idempotent init)
    if utility.has_collection(COLLECTION_NAME):
        print(f"Dropping existing collection: {COLLECTION_NAME}")
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(
            name="id", dtype=DataType.VARCHAR,
            max_length=36, is_primary=True, auto_id=False
        ),
        FieldSchema(
            name="answer_vector", dtype=DataType.FLOAT_VECTOR,
            dim=DIMENSION
        ),
        FieldSchema(
            name="question_sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR
        ),
        FieldSchema(
            name="category_id", dtype=DataType.VARCHAR,
            max_length=36, default_value=""
        ),
        FieldSchema(
            name="tags", dtype=DataType.ARRAY,
            element_type=DataType.VARCHAR, max_capacity=20,
            max_length=50,
        ),
        FieldSchema(
            name="difficulty", dtype=DataType.VARCHAR,
            max_length=10, default_value="medium"
        ),
        FieldSchema(
            name="version", dtype=DataType.INT64,
            default_value=1
        ),
        FieldSchema(
            name="is_deleted", dtype=DataType.BOOL,
            default_value=False
        ),
        FieldSchema(
            name="created_at", dtype=DataType.INT64,
        ),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="Knowledge base answer vectors for hybrid retrieval + RAG evaluation",
        enable_dynamic_field=True
    )

    collection = Collection(name=COLLECTION_NAME, schema=schema)

    # Dense vector index
    collection.create_index(
        field_name="answer_vector",
        index_params={
            "metric_type": "COSINE",
            "index_type": "IVF_SQ8",
            "params": {"nlist": 1024}
        },
        index_name="idx_answer_vector"
    )

    # Sparse vector index
    collection.create_index(
        field_name="question_sparse_vector",
        index_params={
            "metric_type": "IP",
            "index_type": "SPARSE_INVERTED_INDEX",
            "params": {}
        },
        index_name="idx_question_sparse"
    )

    # Scalar indexes
    collection.create_index(field_name="is_deleted", index_name="idx_is_deleted")
    collection.create_index(field_name="category_id", index_name="idx_category_id")

    collection.load()
    print(f"Collection '{COLLECTION_NAME}' created and loaded. Entities: {collection.num_entities}")


if __name__ == "__main__":
    init_collection()
