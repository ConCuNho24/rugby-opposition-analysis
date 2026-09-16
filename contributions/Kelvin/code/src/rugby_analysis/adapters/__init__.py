"""Source adapters isolate external schemas from the canonical model."""

from rugby_analysis.adapters.public_dataset import CodeProcessorVideoAnnotationAdapter
from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter

__all__ = ["CodeProcessorVideoAnnotationAdapter", "RugbyDataJsonAdapter"]
