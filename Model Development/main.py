from preprocessing import PreprocessingPipeline
from analytics_engine import analyze_batch

pipeline = PreprocessingPipeline()

result = pipeline.ingest_path("data")

analysis = analyze_batch(result)

print(analysis)