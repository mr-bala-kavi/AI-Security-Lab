"""
AI Security Lab - Adversarial Attack Utilities
Implements FGSM and other adversarial attack methods.

Module 5: Adversarial Examples

Based on the PyTorch FGSM Tutorial:
https://pytorch.org/tutorials/beginner/fgsm_tutorial.html
"""
import io
import base64
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def fgsm_attack(image_tensor, epsilon: float, gradient):
    """
    Fast Gradient Sign Method (FGSM) attack.

    Perturbs the image in the direction of the gradient to maximize loss.

    Args:
        image_tensor: Original image tensor
        epsilon: Perturbation magnitude
        gradient: Gradient of loss with respect to image

    Returns:
        Perturbed image tensor
    """
    import torch

    # Collect the element-wise sign of the data gradient
    sign_gradient = gradient.sign()

    # Create the perturbed image by adding epsilon * sign of gradient
    perturbed_image = image_tensor + epsilon * sign_gradient

    # Clamp to maintain valid image range [0, 1] after denormalization
    # Note: We're working with normalized images, so clamping happens differently
    perturbed_image = torch.clamp(perturbed_image, -3, 3)  # Approximate bounds for normalized images

    return perturbed_image


def generate_adversarial_example(classifier, image_file, epsilon: float = 0.1) -> Dict[str, Any]:
    """
    Generate an adversarial example using FGSM attack.

    Args:
        classifier: ImageClassifier instance
        image_file: Input image file
        epsilon: Perturbation magnitude (higher = more visible, more effective)

    Returns:
        Dictionary with attack results
    """
    try:
        import torch
        import torch.nn.functional as F
        from PIL import Image
        import numpy as np

        from models.image_classifier import preprocess_image, tensor_to_image

        # Check if model is available
        model = classifier.get_model()
        if model is None:
            return _fallback_adversarial_result(epsilon)

        model.eval()

        # Preprocess image
        input_tensor = preprocess_image(image_file)
        if input_tensor is None:
            return {'success': False, 'error': 'Failed to preprocess image'}

        # Get original prediction
        orig_class_id, orig_confidence, orig_class_name = classifier.classify_tensor(input_tensor)

        # Enable gradient computation
        input_tensor.requires_grad = True

        # Forward pass
        output = model(input_tensor)

        # Get the target (original class)
        target = torch.tensor([orig_class_id])

        # Calculate loss
        loss = F.cross_entropy(output, target)

        # Backward pass
        model.zero_grad()
        loss.backward()

        # Get gradient
        gradient = input_tensor.grad.data

        # Generate adversarial example using FGSM
        perturbed_tensor = fgsm_attack(input_tensor, epsilon, gradient)

        # Get adversarial prediction
        adv_class_id, adv_confidence, adv_class_name = classifier.classify_tensor(perturbed_tensor)

        # Check if attack was successful (prediction changed)
        attack_successful = orig_class_id != adv_class_id

        # Calculate perturbation metrics
        perturbation = (perturbed_tensor - input_tensor).detach()
        l2_norm = torch.norm(perturbation).item()
        linf_norm = torch.max(torch.abs(perturbation)).item()

        # Convert tensors to images for display
        original_image = tensor_to_image(input_tensor)
        adversarial_image = tensor_to_image(perturbed_tensor)
        perturbation_image = _visualize_perturbation(perturbation)

        # Encode images to base64 for JSON response
        result = {
            'success': True,
            'attack_successful': attack_successful,
            'epsilon': epsilon,
            'original': {
                'class_id': orig_class_id,
                'class_name': orig_class_name,
                'confidence': round(orig_confidence * 100, 2)
            },
            'adversarial': {
                'class_id': adv_class_id,
                'class_name': adv_class_name,
                'confidence': round(adv_confidence * 100, 2)
            },
            'metrics': {
                'l2_norm': round(l2_norm, 6),
                'linf_norm': round(linf_norm, 6),
                'prediction_changed': attack_successful
            }
        }

        # Add image data if conversion successful
        if original_image:
            result['images'] = {
                'original': _image_to_base64(original_image),
                'adversarial': _image_to_base64(adversarial_image),
                'perturbation': _image_to_base64(perturbation_image) if perturbation_image else None
            }

        return result

    except Exception as e:
        logger.error(f"Adversarial generation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def _visualize_perturbation(perturbation_tensor) -> Optional['Image.Image']:
    """
    Visualize the perturbation (amplified for visibility).

    Args:
        perturbation_tensor: The perturbation added to the image

    Returns:
        PIL Image showing amplified perturbation
    """
    try:
        import torch
        from PIL import Image
        import numpy as np

        # Remove batch dimension
        if perturbation_tensor.dim() == 4:
            perturbation_tensor = perturbation_tensor.squeeze(0)

        # Detach and move to CPU
        pert = perturbation_tensor.detach().cpu()

        # Normalize perturbation for visualization
        # Scale to [-1, 1] then to [0, 1]
        pert_normalized = (pert - pert.min()) / (pert.max() - pert.min() + 1e-8)

        # Amplify for visibility
        pert_amplified = torch.clamp(pert_normalized * 10, 0, 1)

        # Convert to numpy
        np_pert = pert_amplified.permute(1, 2, 0).numpy()
        np_pert = (np_pert * 255).astype(np.uint8)

        return Image.fromarray(np_pert)

    except Exception as e:
        logger.error(f"Perturbation visualization error: {e}")
        return None


def _image_to_base64(image) -> Optional[str]:
    """Convert PIL Image to base64 string."""
    if image is None:
        return None

    try:
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Image to base64 error: {e}")
        return None


def _fallback_adversarial_result(epsilon: float) -> Dict[str, Any]:
    """Generate fallback result when model is unavailable."""
    return {
        'success': True,
        'attack_successful': True,
        'epsilon': epsilon,
        'original': {
            'class_id': 281,
            'class_name': 'tabby cat',
            'confidence': 85.5
        },
        'adversarial': {
            'class_id': 207,
            'class_name': 'golden retriever',
            'confidence': 72.3
        },
        'metrics': {
            'l2_norm': 0.0425,
            'linf_norm': epsilon,
            'prediction_changed': True
        },
        'note': 'Using simulated results (model not loaded)'
    }


def pgd_attack(model, image_tensor, target_class: int, epsilon: float = 0.1,
              alpha: float = 0.01, num_iterations: int = 40) -> 'torch.Tensor':
    """
    Projected Gradient Descent (PGD) attack.

    More powerful than FGSM, uses iterative updates.

    Args:
        model: The classifier model
        image_tensor: Original image tensor
        target_class: Target class for untargeted attack
        epsilon: Maximum perturbation
        alpha: Step size per iteration
        num_iterations: Number of iterations

    Returns:
        Adversarial image tensor
    """
    import torch
    import torch.nn.functional as F

    # Start from random perturbation within epsilon ball
    perturbed = image_tensor.clone().detach()
    perturbed = perturbed + torch.empty_like(perturbed).uniform_(-epsilon, epsilon)
    perturbed = torch.clamp(perturbed, -3, 3)

    for _ in range(num_iterations):
        perturbed.requires_grad = True

        output = model(perturbed)
        loss = F.cross_entropy(output, torch.tensor([target_class]))

        model.zero_grad()
        loss.backward()

        # Update with gradient ascent (maximize loss)
        with torch.no_grad():
            perturbed = perturbed + alpha * perturbed.grad.sign()

            # Project back to epsilon ball around original
            delta = torch.clamp(perturbed - image_tensor, -epsilon, epsilon)
            perturbed = torch.clamp(image_tensor + delta, -3, 3)

    return perturbed.detach()


def calculate_attack_metrics(original_tensor, adversarial_tensor) -> Dict[str, float]:
    """
    Calculate various metrics for adversarial perturbation.

    Args:
        original_tensor: Original image tensor
        adversarial_tensor: Adversarial image tensor

    Returns:
        Dictionary of metrics
    """
    import torch

    perturbation = adversarial_tensor - original_tensor

    return {
        'l0_norm': torch.count_nonzero(perturbation).item(),
        'l1_norm': torch.norm(perturbation, p=1).item(),
        'l2_norm': torch.norm(perturbation, p=2).item(),
        'linf_norm': torch.max(torch.abs(perturbation)).item(),
        'mean_perturbation': torch.mean(torch.abs(perturbation)).item(),
        'std_perturbation': torch.std(perturbation).item()
    }
