# RAG Service Threshold Improvements

## Overview

This document describes the improvements made to the RAG service's similarity threshold handling and context filtering to ensure higher quality responses and better handling of edge cases.

## Changes Implemented

### 1. Explicit Similarity Threshold (0.75)

**Before**: Default threshold was 0.2, allowing many low-quality matches
**After**: Default threshold increased to 0.75 for higher quality matches

```python
# Old configuration
self.default_rpc_threshold = float(os.getenv("DEFAULT_RPC_THRESHOLD", 0.2))

# New configuration  
self.default_rpc_threshold = float(os.getenv("DEFAULT_RPC_THRESHOLD", 0.75))
```

### 2. Enhanced Context Filtering

#### Vector Search Filtering
- **Post-filtering**: Documents returned by RPC are filtered again to ensure they meet the threshold
- **Score validation**: Each document's similarity score is checked against the threshold
- **Logging**: Filtered documents are logged for debugging

#### BM25 Search Filtering
- **Score normalization**: BM25 scores are normalized to 0-1 range
- **Threshold filtering**: Only documents above the BM25 threshold (0.3) are included
- **Enhanced metadata**: Includes both raw and normalized scores

### 3. Graceful Handling of No Relevant Documents

#### Adaptive Threshold System
- **Progressive threshold reduction**: If no documents found with high threshold, automatically tries lower thresholds
- **Configurable steps**: [0.75, 0.6, 0.4, 0.2] by default
- **Minimum document count**: Ensures at least 1 document is found before proceeding

#### Fallback Responses
- **Informative messages**: When no relevant documents found, provides helpful response
- **User guidance**: Suggests reformulating query or contacting SIPEN directly
- **No crashes**: System continues to function even with no matches

## New Configuration Options

### Environment Variables

```bash
# Core threshold settings
DEFAULT_RPC_THRESHOLD=0.75          # Vector search threshold
BM25_SCORE_THRESHOLD=0.3            # BM25 search threshold
MIN_DOCUMENT_COUNT=1                # Minimum documents required

# Adaptive threshold settings
ADAPTIVE_THRESHOLD_ENABLED=true     # Enable adaptive threshold
```

### Configuration Class Properties

```python
class RAGConfig:
    # Threshold settings
    default_rpc_threshold = 0.75
    bm25_score_threshold = 0.3
    min_document_count = 1
    
    # Adaptive threshold
    adaptive_threshold_enabled = True
    adaptive_threshold_steps = [0.75, 0.6, 0.4, 0.2]
```

## Enhanced Response Format

The RAG service now returns additional metadata about the search quality:

```json
{
  "answer": "Response text...",
  "source_documents": [...],
  "parameters_used": {...},
  "confidence_score": 0.85,
  "document_count": 5,
  "unique_sources_count": 3,
  "warning": null
}
```

### New Response Fields

- **confidence_score**: Average similarity score of retrieved documents (0-1)
- **document_count**: Total number of documents retrieved
- **unique_sources_count**: Number of unique source documents
- **warning**: Warning message if insufficient documents found

## Source Document Enhancements

Source documents now include more detailed metadata:

```json
{
  "source_name": "ley_87_01.pdf",
  "url": "https://www.sipen.gob.do/descarga/ley_87_01.pdf",
  "doc_type": "leyes",
  "avg_score": 0.82,
  "retriever_type": "vector"
}
```

### Enhanced Metadata Fields

- **avg_score**: Average similarity score for this source
- **retriever_type**: Whether document came from "vector" or "bm25" search
- **doc_type**: Document type for proper URL generation

## Testing

Run the threshold improvements test:

```bash
cd Testing
python test_threshold_improvements.py
```

### Test Coverage

1. **Threshold Configuration**: Verifies new default values
2. **Adaptive Threshold**: Tests progressive threshold reduction
3. **Score Filtering**: Ensures low-quality documents are filtered
4. **No Documents Handling**: Tests graceful handling of edge cases
5. **Confidence Scoring**: Validates confidence score calculations

## Benefits

### Quality Improvement
- **Higher relevance**: Only high-similarity documents are used
- **Better answers**: Reduced noise from low-quality matches
- **Consistent quality**: Standardized threshold across all searches

### Reliability
- **No crashes**: Graceful handling of edge cases
- **Adaptive behavior**: Automatically adjusts to find relevant content
- **Better error messages**: Informative responses when no matches found

### Monitoring
- **Detailed logging**: Track filtering and threshold decisions
- **Confidence scores**: Monitor response quality
- **Performance metrics**: Document counts and source diversity

## Migration Notes

### Breaking Changes
- Default threshold increased from 0.2 to 0.75
- Some queries may return fewer documents
- Response format includes new fields

### Backward Compatibility
- All existing API endpoints remain unchanged
- Optional new fields don't break existing clients
- Environment variables can override new defaults

## Troubleshooting

### No Documents Found
1. Check if adaptive threshold is enabled
2. Verify database connection and content
3. Try reformulating the query
4. Check logs for threshold decisions

### Low Confidence Scores
1. Review document quality in database
2. Consider adjusting thresholds
3. Check embedding model performance
4. Verify query relevance to domain

### Performance Issues
1. Monitor adaptive threshold steps
2. Check document filtering overhead
3. Review logging verbosity
4. Consider caching strategies 