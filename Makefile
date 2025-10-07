.PHONY: rag-update

rag-update:
	python scripts/ingest_docs.py
	@if git diff --quiet -- docs/rag_vectors/corpus.parquet; then \
		echo "Vectors unchanged; skipping commit."; \
	else \
		git add docs/rag_vectors/corpus.parquet; \
		git commit -m "Update RAG vectors"; \
		git push; \
	fi
