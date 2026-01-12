"""
AI Security Lab - Image Classifier
Image classification model for adversarial examples demonstration.

Module 5: Adversarial Examples

Uses MobileNetV2 for efficient classification.
"""
import io
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ImageNet class labels (subset for common objects)
IMAGENET_CLASSES = {
    0: 'tench', 1: 'goldfish', 2: 'great white shark', 3: 'tiger shark',
    4: 'hammerhead', 5: 'electric ray', 6: 'stingray', 7: 'cock',
    8: 'hen', 9: 'ostrich', 10: 'brambling', 11: 'goldfinch',
    207: 'golden retriever', 208: 'Labrador retriever', 209: 'Chesapeake Bay retriever',
    281: 'tabby cat', 282: 'tiger cat', 283: 'Persian cat', 284: 'Siamese cat',
    285: 'Egyptian cat', 386: 'African elephant', 387: 'Indian elephant',
    388: 'lesser panda', 389: 'giant panda', 948: 'orange', 949: 'banana',
    950: 'strawberry', 951: 'orange', 952: 'pineapple', 953: 'banana',
    954: 'jackfruit', 955: 'custard apple', 956: 'pomegranate',
    957: 'hay', 958: 'carbonara', 959: 'chocolate sauce'
}


class ImageClassifier:
    """
    Image classifier using MobileNetV2.

    Provides methods for classification and is vulnerable to
    adversarial perturbations (FGSM attack).
    """

    def __init__(self):
        """Initialize the classifier."""
        self.model = None
        self.transform = None
        self._load_model()

    def _load_model(self):
        """Load the MobileNetV2 model."""
        try:
            import torch
            import torchvision.transforms as transforms
            from models.model_manager import ModelManager

            self.model = ModelManager.get_image_classifier()

            if self.model is not None:
                self.transform = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]
                    )
                ])
                logger.info("Image classifier loaded successfully")
            else:
                logger.warning("Image classifier not available, using fallback")

        except Exception as e:
            logger.error(f"Failed to load image classifier: {e}")
            self.model = None

    def classify(self, image_file) -> Dict[str, Any]:
        """
        Classify an uploaded image.

        Args:
            image_file: File-like object or path to image

        Returns:
            Classification results
        """
        if self.model is None:
            return self._fallback_classify()

        try:
            import torch
            from PIL import Image

            # Load image
            if hasattr(image_file, 'read'):
                image = Image.open(image_file).convert('RGB')
            else:
                image = Image.open(image_file).convert('RGB')

            # Transform and classify
            input_tensor = self.transform(image).unsqueeze(0)

            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

            # Get top 5 predictions
            top5_prob, top5_idx = torch.topk(probabilities, 5)

            predictions = []
            for i, (prob, idx) in enumerate(zip(top5_prob, top5_idx)):
                class_name = self._get_class_name(idx.item())
                predictions.append({
                    'rank': i + 1,
                    'class_id': idx.item(),
                    'class_name': class_name,
                    'confidence': round(prob.item() * 100, 2)
                })

            return {
                'success': True,
                'predictions': predictions,
                'top_prediction': predictions[0]['class_name'],
                'top_confidence': predictions[0]['confidence']
            }

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                'success': False,
                'error': str(e),
                'predictions': []
            }

    def classify_tensor(self, input_tensor) -> Tuple[int, float, str]:
        """
        Classify a preprocessed tensor.

        Args:
            input_tensor: Preprocessed image tensor

        Returns:
            Tuple of (class_id, confidence, class_name)
        """
        import torch

        if self.model is None:
            return 0, 0.5, "unknown"

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

        top_prob, top_idx = torch.max(probabilities, 0)

        return (
            top_idx.item(),
            top_prob.item(),
            self._get_class_name(top_idx.item())
        )

    def get_model(self):
        """Get the underlying PyTorch model."""
        return self.model

    def get_transform(self):
        """Get the image transform pipeline."""
        return self.transform

    def _get_class_name(self, class_id: int) -> str:
        """Get human-readable class name."""
        # Try to get from our subset
        if class_id in IMAGENET_CLASSES:
            return IMAGENET_CLASSES[class_id]

        # Load full ImageNet labels if available
        try:
            import json
            labels_path = Path(__file__).parent / 'imagenet_labels.json'
            if labels_path.exists():
                with open(labels_path) as f:
                    labels = json.load(f)
                    return labels.get(str(class_id), f"class_{class_id}")
        except Exception:
            pass

        return f"class_{class_id}"

    def _fallback_classify(self) -> Dict[str, Any]:
        """Fallback classification when model unavailable."""
        return {
            'success': True,
            'predictions': [
                {'rank': 1, 'class_id': 281, 'class_name': 'tabby cat', 'confidence': 45.5},
                {'rank': 2, 'class_id': 282, 'class_name': 'tiger cat', 'confidence': 23.2},
                {'rank': 3, 'class_id': 207, 'class_name': 'golden retriever', 'confidence': 15.8},
                {'rank': 4, 'class_id': 948, 'class_name': 'orange', 'confidence': 8.3},
                {'rank': 5, 'class_id': 949, 'class_name': 'banana', 'confidence': 7.2},
            ],
            'top_prediction': 'tabby cat',
            'top_confidence': 45.5,
            'note': 'Using fallback classification (model not loaded)'
        }


def preprocess_image(image_path_or_file) -> Optional['torch.Tensor']:
    """
    Preprocess an image for the classifier.

    Args:
        image_path_or_file: Path or file-like object

    Returns:
        Preprocessed tensor or None
    """
    try:
        import torch
        import torchvision.transforms as transforms
        from PIL import Image

        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        if hasattr(image_path_or_file, 'read'):
            image = Image.open(image_path_or_file).convert('RGB')
        else:
            image = Image.open(image_path_or_file).convert('RGB')

        tensor = transform(image).unsqueeze(0)
        tensor.requires_grad = True

        return tensor

    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")
        return None


def tensor_to_image(tensor, denormalize: bool = True) -> Optional['Image.Image']:
    """
    Convert a tensor back to a PIL Image.

    Args:
        tensor: Image tensor
        denormalize: Whether to reverse normalization

    Returns:
        PIL Image or None
    """
    try:
        import torch
        from PIL import Image
        import numpy as np

        # Remove batch dimension if present
        if tensor.dim() == 4:
            tensor = tensor.squeeze(0)

        # Detach and move to CPU
        tensor = tensor.detach().cpu()

        if denormalize:
            # Reverse normalization
            mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            tensor = tensor * std + mean

        # Clamp to valid range
        tensor = torch.clamp(tensor, 0, 1)

        # Convert to numpy and then PIL
        np_image = tensor.permute(1, 2, 0).numpy()
        np_image = (np_image * 255).astype(np.uint8)

        return Image.fromarray(np_image)

    except Exception as e:
        logger.error(f"Tensor to image conversion error: {e}")
        return None
