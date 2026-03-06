import os
import sys
import traceback
import torch
from typing import Optional, List, Tuple
from .gemini_api import (
    ASPECT_RATIO_OPTIONS,
    DEFAULT_IMAGE_MODEL_LABEL,
    GeminiAPIClient,
    IMAGE_MODEL_LABELS,
    IMAGE_SIZE_OPTIONS,
    MODEL_LABEL_TO_ID,
    get_model_label,
    is_image_generation_model,
    normalize_model_name,
)
import comfy.utils
from comfy.utils import ProgressBar


class NanoBananaGeminiImageNode:
    """
    Generate images using Gemini image models.
    Returns image batches plus any text the model includes in its response.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Text prompt for image generation"
                }),
                "model": (list(IMAGE_MODEL_LABELS), {
                    "default": DEFAULT_IMAGE_MODEL_LABEL,
                    "tooltip": "Gemini image model for generation or editing"
                }),
                "batch_size": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "display": "number",
                    "tooltip": "Number of images to generate (1-4)"
                }),
                "seed": ("INT", {
                    "default": 42,
                    "min": 0,
                    "max": 2147483647,  # Max value for 32-bit signed integer
                    "control_after_generate": "randomize",
                    "tooltip": "Base seed for generation. Sequential seeds used for batch (seed, seed+1, seed+2...)"
                }),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Optional system prompt to guide the model's behavior"
                }),
                "images": ("IMAGE", {
                    "tooltip": "Optional image(s) to use as context or reference"
                }),
                "api_key": ("STRING", {
                    "default": "",
                    "tooltip": "Gemini API key (leave empty to use GEMINI_API_KEY env variable)",
                    "multiline": False,
                    "dynamicPrompts": False,
                    "password": True
                }),
                "aspect_ratio": (list(ASPECT_RATIO_OPTIONS), {
                    "default": "auto",
                    "tooltip": "Image models only. Sets output aspect ratio. 'auto' lets the model decide."
                }),
                "image_size": (list(IMAGE_SIZE_OPTIONS), {
                    "default": "auto",
                    "tooltip": "Gemini 3 image models only. Controls output resolution; ignored for Nano Banana 2.5."
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "text")
    FUNCTION = "generate"
    CATEGORY = "Nano Banana"
    DESCRIPTION = "Generate images with Gemini image models"

    @classmethod
    def VALIDATE_INPUTS(cls, model: str, **kwargs):
        # Accept both display labels and raw model IDs (for saved workflows)
        if model in MODEL_LABEL_TO_ID or normalize_model_name(model) != model:
            return True
        if is_image_generation_model(model):
            return True
        return f"Unknown model: {model}"

    def generate(
        self,
        prompt: str,
        model: str,
        batch_size: int,
        seed: int,
        system_prompt: str = "",
        images: Optional[torch.Tensor] = None,
        api_key: str = "",
        aspect_ratio: str = "auto",
        image_size: str = "auto",
    ) -> Tuple[torch.Tensor, str]:
        
        # Validate inputs
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if seed < 0 or seed > 2147483647:
            raise ValueError(f"Seed must be between 0 and 2147483647 (32-bit integer range), got {seed}")

        model = normalize_model_name(model)

        if not is_image_generation_model(model):
            raise ValueError(f"Unsupported model for this node: {model}. Use a Gemini image model.")
        
        # Get API key
        api_key = api_key if api_key else os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("No API key provided. Set GEMINI_API_KEY environment variable or provide API key in the node.")
        
        # Basic validation of API key format (Gemini keys typically start with "AI")
        if api_key and len(api_key) < 10:
            raise ValueError("API key appears to be invalid (too short). Please check your API key.")
        
        try:
            client = GeminiAPIClient(api_key=api_key)
            
            image_list = None
            if images is not None:
                image_list = []
                if images.dim() == 4:
                    for i in range(images.shape[0]):
                        image_list.append(images[i:i+1])
                else:
                    image_list.append(images.unsqueeze(0))
            
            # Use concurrent batch processing for batch_size > 1
            if batch_size > 1:
                print(f"[NanoBanana Gemini] Starting concurrent batch generation for {batch_size} items...")
                
                # Create progress bar for batch generation
                pbar = ProgressBar(batch_size)
                
                # Prepare configurations for each batch item
                batch_configs = []
                for i in range(batch_size):
                    current_seed = seed + i
                    config = {
                        'prompt': prompt,
                        'system_prompt': system_prompt if system_prompt else None,
                        'images': image_list,
                        'seed': current_seed,
                        'aspect_ratio': aspect_ratio,
                        'image_size': image_size,
                    }
                    batch_configs.append(config)
                
                # Execute concurrent batch generation with progress callback
                def progress_callback(completed_index):
                    pbar.update(1)
                    
                results = client.generate_batch_concurrent(
                    prompts_configs=batch_configs,
                    model=model,
                    progress_callback=progress_callback
                )
                
                # Process results
                all_output_images = []
                all_text_responses = []
                model_label = get_model_label(model)
                
                for i, result in enumerate(results):
                    current_seed = seed + i
                    output_images, text_response = result
                    # For batch, we expect one image per request to maintain batch_size
                    # If multiple images returned, take the first one
                    if output_images and len(output_images) > 0:
                        all_output_images.append(output_images[0])
                    else:
                        all_output_images.append(torch.zeros((1, 64, 64, 4)))
                    all_text_responses.append(f"[Batch {i+1}/{batch_size}, {model_label}, Seed: {current_seed}]\n{text_response}")
            else:
                # Single generation
                all_output_images = []
                all_text_responses = []
                
                print(f"[NanoBanana Gemini] Generating with seed {seed}...")
                
                # Create progress bar for single generation (indeterminate)
                pbar = ProgressBar(1)

                output_images, text_response = client.generate_image(
                    prompt=prompt,
                    model=model,
                    images=image_list,
                    seed=seed,
                    system_prompt=system_prompt if system_prompt else None,
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                )
                all_output_images.extend(output_images)
                all_text_responses.append(text_response)
                
                # Complete the progress bar
                pbar.update(1)
            
            # Combine all results
            if all_output_images:
                # Ensure all images have the same dimensions before concatenation
                # Use the first image's dimensions as reference
                ref_h = all_output_images[0].shape[1]
                ref_w = all_output_images[0].shape[2]
                
                resized_outputs: List[torch.Tensor] = []
                for img in all_output_images:
                    if img.shape[1] != ref_h or img.shape[2] != ref_w:
                        # Resize to match reference dimensions
                        upscaled = comfy.utils.common_upscale(
                            img.movedim(-1, 1),  # BHWC -> BCHW
                            ref_w,
                            ref_h,
                            "bilinear",
                            "center",
                        ).movedim(1, -1)  # BCHW -> BHWC
                        resized_outputs.append(upscaled)
                    else:
                        resized_outputs.append(img)
                
                result_tensor = torch.cat(resized_outputs, dim=0)
            else:
                result_tensor = torch.zeros((batch_size, 64, 64, 4))
            
            # Join all text responses
            combined_text = "\n\n".join(all_text_responses)
            
            return (result_tensor, combined_text)
            
        except Exception as e:
            error_msg = str(e)
            
            # Log the full error details
            print(f"[NanoBanana Gemini] Error: {error_msg}", file=sys.stderr)
            
            # Check for specific error types and provide helpful messages
            if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                raise RuntimeError("Invalid API key. Please check your Gemini API key in Google AI Studio.")
            elif "UNAUTHENTICATED" in error_msg:
                raise RuntimeError("Authentication failed. Please verify your API key has the correct permissions.")
            elif "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                raise RuntimeError("API quota exceeded. Please check your usage limits in Google AI Studio.")
            elif "INVALID_ARGUMENT" in error_msg:
                if "model" in error_msg.lower():
                    raise RuntimeError(f"Invalid model specified. Please use one of the supported models.")
                elif "seed" in error_msg.lower():
                    raise RuntimeError(f"Invalid seed value. Must be between 0 and 2147483647.")
                else:
                    raise RuntimeError(f"Invalid argument: {error_msg}")
            elif "PERMISSION_DENIED" in error_msg:
                raise RuntimeError("Permission denied. Your API key may not have access to this model or feature.")
            elif "NOT_FOUND" in error_msg:
                raise RuntimeError("Resource not found. The model or endpoint may not be available.")
            elif "rate limit" in error_msg.lower() or "429" in str(e):
                raise RuntimeError("Rate limit exceeded. Please wait a moment and try again.")
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                raise RuntimeError("Request timed out. Try reducing batch size or prompt complexity.")
            elif "connection" in error_msg.lower():
                raise RuntimeError("Connection error. Please check your internet connection.")
            else:
                # For unknown errors, show the full error with traceback
                print(f"[NanoBanana Gemini] Full traceback:\n{traceback.format_exc()}", file=sys.stderr)
                raise RuntimeError(f"Gemini API Error: {error_msg}")


class BatchImages:
    """Combine a dynamic number of IMAGE inputs into a single IMAGE batch.

    Images with mismatched spatial sizes are resized to match the first image
    using bilinear upscaling and centered alignment, mirroring ComfyUI's
    common_upscale behavior in similar nodes.
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Frontend JS dynamically adds IMAGE inputs; keep declarations empty
        return {
            "required": {},
            "optional": {},
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "batch"
    CATEGORY = "image"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        # Accept dynamic inputs; validation handled at runtime
        return True

    def batch(self, **kwargs):
        # Collect all connected IMAGE tensors regardless of input names
        image_tensors: List[torch.Tensor] = [
            value for value in kwargs.values() if isinstance(value, torch.Tensor)
        ]

        if len(image_tensors) == 0:
            # Fallback to a 1x64x64x4 zero image to avoid crashes
            return (torch.zeros((1, 64, 64, 4)),)

        # Use the first provided image as reference size
        reference = image_tensors[0]
        ref_h, ref_w = reference.shape[1], reference.shape[2]

        # Resize all non-matching images to reference HxW
        resized_images: List[torch.Tensor] = []
        for img in image_tensors:
            if img.shape[1] != ref_h or img.shape[2] != ref_w:
                # comfy.utils.common_upscale expects BCHW tensors
                upscaled = comfy.utils.common_upscale(
                    img.movedim(-1, 1),
                    ref_w,
                    ref_h,
                    "bilinear",
                    "center",
                ).movedim(1, -1)
                resized_images.append(upscaled)
            else:
                resized_images.append(img)

        # Concatenate along batch dimension
        batched = torch.cat(resized_images, dim=0)
        return (batched,)


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "NanoBananaGeminiImageNode": NanoBananaGeminiImageNode,
    "BatchImages": BatchImages,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "NanoBananaGeminiImageNode": "Nano Banana Gemini",
    "BatchImages": "Batch Images",
}
