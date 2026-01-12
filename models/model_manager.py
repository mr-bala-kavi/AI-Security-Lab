"""
AI Security Lab - Model Manager
Handles lazy loading and caching of ML models for the vulnerability modules.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Model cache
_models = {}
_tokenizers = {}


class ModelManager:
    """
    Centralized model management with lazy loading and caching.

    Models are only loaded when first requested, then cached for reuse.
    This prevents slow startup times and reduces memory usage.
    """

    # Model paths (relative to cache directory)
    MODELS = {
        'distilgpt2': 'distilgpt2',
        'sentiment': 'distilbert-base-uncased-finetuned-sst-2-english',
        'mobilenet': 'mobilenet_v2',
    }

    @classmethod
    def get_cache_dir(cls) -> Path:
        """Get the model cache directory."""
        from config import Config
        cache_dir = Path(Config.MODEL_CACHE_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @classmethod
    def get_text_generator(cls) -> Tuple[Any, Any]:
        """
        Get DistilGPT2 model and tokenizer for text generation.

        Used in: Prompt Injection (Module 1), Model Inversion (Module 4)

        Returns:
            Tuple of (model, tokenizer)
        """
        if 'distilgpt2' not in _models:
            try:
                logger.info("Loading DistilGPT2 model...")
                from transformers import GPT2LMHeadModel, GPT2Tokenizer

                tokenizer = GPT2Tokenizer.from_pretrained(
                    cls.MODELS['distilgpt2'],
                    cache_dir=cls.get_cache_dir()
                )
                tokenizer.pad_token = tokenizer.eos_token

                model = GPT2LMHeadModel.from_pretrained(
                    cls.MODELS['distilgpt2'],
                    cache_dir=cls.get_cache_dir()
                )
                model.eval()

                _models['distilgpt2'] = model
                _tokenizers['distilgpt2'] = tokenizer
                logger.info("DistilGPT2 loaded successfully")

            except Exception as e:
                logger.warning(f"Failed to load DistilGPT2: {e}")
                logger.info("Using rule-based fallback for text generation")
                _models['distilgpt2'] = None
                _tokenizers['distilgpt2'] = None

        return _models.get('distilgpt2'), _tokenizers.get('distilgpt2')

    @classmethod
    def get_sentiment_classifier(cls) -> Any:
        """
        Get DistilBERT sentiment analysis pipeline.

        Used in: Training Data Poisoning (Module 3)

        Returns:
            Hugging Face pipeline for sentiment analysis
        """
        if 'sentiment' not in _models:
            try:
                logger.info("Loading sentiment classifier...")
                from transformers import pipeline

                classifier = pipeline(
                    'sentiment-analysis',
                    model=cls.MODELS['sentiment'],
                    tokenizer=cls.MODELS['sentiment'],
                    model_kwargs={'cache_dir': cls.get_cache_dir()},
                    tokenizer_kwargs={'cache_dir': cls.get_cache_dir()}
                )

                _models['sentiment'] = classifier
                logger.info("Sentiment classifier loaded successfully")

            except Exception as e:
                logger.warning(f"Failed to load sentiment classifier: {e}")
                logger.info("Using rule-based fallback for sentiment")
                _models['sentiment'] = None

        return _models.get('sentiment')

    @classmethod
    def get_image_classifier(cls) -> Any:
        """
        Get MobileNetV2 for image classification.

        Used in: Adversarial Examples (Module 5)

        Returns:
            PyTorch MobileNetV2 model
        """
        if 'mobilenet' not in _models:
            try:
                logger.info("Loading MobileNetV2...")
                import torch
                import torchvision.models as models

                model = models.mobilenet_v2(pretrained=True)
                model.eval()

                _models['mobilenet'] = model
                logger.info("MobileNetV2 loaded successfully")

            except Exception as e:
                logger.warning(f"Failed to load MobileNetV2: {e}")
                _models['mobilenet'] = None

        return _models.get('mobilenet')

    @classmethod
    def unload_model(cls, model_name: str) -> None:
        """
        Unload a model from cache to free memory.

        Args:
            model_name: Name of the model to unload
        """
        if model_name in _models:
            del _models[model_name]
            logger.info(f"Unloaded model: {model_name}")

        if model_name in _tokenizers:
            del _tokenizers[model_name]

    @classmethod
    def unload_all(cls) -> None:
        """Unload all models from cache."""
        _models.clear()
        _tokenizers.clear()
        logger.info("All models unloaded")

    @classmethod
    def get_loaded_models(cls) -> list:
        """Get list of currently loaded models."""
        return list(_models.keys())

    @classmethod
    def is_model_available(cls, model_name: str) -> bool:
        """Check if a model is available (loaded and not None)."""
        return model_name in _models and _models[model_name] is not None


def generate_text_with_model(prompt: str, max_length: int = 100) -> str:
    """
    Generate text using DistilGPT2.

    Falls back to rule-based response if model unavailable.

    Args:
        prompt: Input prompt for generation
        max_length: Maximum length of generated text

    Returns:
        Generated text
    """
    model, tokenizer = ModelManager.get_text_generator()

    if model is None or tokenizer is None:
        # Fallback to rule-based response
        return _rule_based_response(prompt)

    try:
        import torch

        inputs = tokenizer.encode(prompt, return_tensors='pt', truncation=True, max_length=512)

        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=2
            )

        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove the prompt from the output if it's included
        if generated.startswith(prompt):
            generated = generated[len(prompt):].strip()

        return generated

    except Exception as e:
        logger.error(f"Text generation error: {e}")
        return _rule_based_response(prompt)


def _rule_based_response(prompt: str) -> str:
    """
    Simple rule-based response for when models aren't available.

    Args:
        prompt: User input

    Returns:
        Generated response
    """
    prompt_lower = prompt.lower()

    # Common patterns and responses
    if any(word in prompt_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! How can I help you today?"

    if any(word in prompt_lower for word in ['help', 'assist', 'support']):
        return "I'm here to help! What would you like to know?"

    if 'password' in prompt_lower or 'secret' in prompt_lower:
        return "I cannot share sensitive information."

    if any(word in prompt_lower for word in ['ignore', 'forget', 'disregard']):
        return "I understand your request. How else can I assist you?"

    if '?' in prompt:
        return "That's an interesting question. Let me think about it..."

    return "I understand. Is there anything specific you'd like to discuss?"


def classify_sentiment_with_model(text: str) -> dict:
    """
    Classify sentiment using DistilBERT.

    Falls back to rule-based sentiment if model unavailable.

    Args:
        text: Input text to classify

    Returns:
        Dictionary with label and score
    """
    classifier = ModelManager.get_sentiment_classifier()

    if classifier is None:
        # Fallback to rule-based sentiment
        return _rule_based_sentiment(text)

    try:
        result = classifier(text, truncation=True, max_length=512)[0]
        return {
            'label': result['label'],
            'score': round(result['score'], 4)
        }
    except Exception as e:
        logger.error(f"Sentiment classification error: {e}")
        return _rule_based_sentiment(text)


def _rule_based_sentiment(text: str) -> dict:
    """
    Simple rule-based sentiment analysis.

    Args:
        text: Input text

    Returns:
        Dictionary with label and score
    """
    positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'happy', 'wonderful', 'fantastic', 'best']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'worst', 'poor', 'sad', 'angry']

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > neg_count:
        return {'label': 'POSITIVE', 'score': min(0.5 + pos_count * 0.1, 0.99)}
    elif neg_count > pos_count:
        return {'label': 'NEGATIVE', 'score': min(0.5 + neg_count * 0.1, 0.99)}
    else:
        return {'label': 'POSITIVE', 'score': 0.5}
