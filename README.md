# Comfy Nano Banana

Google Gemini API integration for ComfyUI focused on Gemini image generation and editing models, plus a dynamic batch images utility node.

## Features

- 🎨 **Image Generation** - Create and edit images with Gemini's current Nano Banana image models
- 📝 **Text Responses** - Capture any text returned alongside generated images
- 🖼️ **Multimodal Support** - Use images as input context for image generation and editing
- 🚀 **Concurrent Batch Processing** - Generate 1-4 images concurrently with progress tracking
- 🔀 **Dynamic Batch Images** - Combine multiple images into a single batch with automatic resizing
- 🔒 **Secure API Key Handling** - Password field masking with smart export behavior
- ⚡ **Smart Model Detection** - Automatically uses the right generation method based on model
- 🆕 **Nano Banana Pro + Nano Banana 2** - Supports the latest Gemini 3 image generation tiers

## Demo

Watch the Comfy Nano Banana custom node in action:

[![Comfy Nano Banana Demo](https://img.youtube.com/vi/yLs5OdTeXZ8/maxresdefault.jpg)](https://youtu.be/yLs5OdTeXZ8)

## Installation

### Via ComfyUI Manager (Recommended)
1. Install [ComfyUI](https://docs.comfy.org/get_started)
2. Install [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
3. Search for "Nano Banana" in ComfyUI-Manager and install
4. Restart ComfyUI

### Manual Installation
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/darkamenosa/comfy_nanobanana.git
cd comfy_nanobanana
pip install -r requirements.txt
```

## Setup

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Set your API key:
   - **Option 1**: Set environment variable `GEMINI_API_KEY`
   - **Option 2**: Enter directly in the node's API key field

## Security & API Key Handling

### 🔐 Smart Export Behavior
This node implements intelligent API key handling for different export scenarios:

#### **Regular Workflow Export** (Save Workflow)
- **API keys are automatically removed** when saving workflows
- Safe for sharing workflows publicly without exposing sensitive credentials
- Recipients must enter their own API key or use environment variables
- Prevents accidental API key exposure when sharing on forums, GitHub, etc.

#### **API Format Export** (Save as API - Developer Mode)
- **API keys are preserved** in the exported JSON
- Designed for developers deploying workflows programmatically
- Convenient for production deployments and automation
- ⚠️ **Developer Warning**: Only share API format exports with trusted parties or systems

### Best Practices
- Use environment variable `GEMINI_API_KEY` for production deployments
- Always review exported files before sharing publicly
- For public workflow sharing, use regular "Save Workflow" option
- For private/automated use, API format export maintains convenience

## Usage

The extension adds two nodes to ComfyUI:

### 1. Nano Banana Gemini Node
Located under the "Nano Banana" category, this node interfaces with Google's Gemini API.

#### Inputs
- **prompt** (required): Text prompt for generation
- **model**: Gemini image model to use (default: `Nano Banana`)
- **batch_size**: Number of images to generate concurrently (1-4)
- **seed**: For reproducible outputs (0-2147483647)
- **system_prompt** (optional): Instructions to guide the model's behavior
- **images** (optional): Input images for context
- **api_key** (optional): Override environment variable
- **aspect_ratio** (optional): Image output ratio for image models (`auto`, `1:1`, `16:9`, etc.)
- **image_size** (optional): Output resolution for Gemini 3 image models (`auto`, `512px`, `1K`, `2K`, `4K`)

#### Outputs
- **images**: Generated or edited image batch
- **text**: Text response from the model

#### Supported Models
- `Nano Banana` (`gemini-2.5-flash-image`)
- `Nano Banana Pro` (`gemini-3-pro-image-preview`)
- `Nano Banana 2` (`gemini-3.1-flash-image-preview`)

Existing workflows that still store raw Gemini model IDs continue to work. The legacy `gemini-2.5-flash-image-preview` value is also accepted as an alias for `Nano Banana`.

### 2. Batch Images Node
Located under the "image" category, this utility node dynamically combines multiple images into a single batch.

#### Features
- **Dynamic Inputs**: Automatically adds/removes image inputs as you connect/disconnect
- **Auto-resize**: Mismatched images are automatically resized to match the first image's dimensions
- **Clean Interface**: Unused inputs are automatically removed
- **Flexible**: Connect any number of images from different sources

#### How to Use
1. Add "Batch Images" node from the image category
2. Connect your first image - the node automatically creates a new input
3. Connect additional images - each connection creates a new input slot
4. Disconnecting removes the unused input automatically
5. All images are resized to match the first image's dimensions and combined into a batch

## Examples

### Image Generation
1. Add "Nano Banana Gemini" node
2. Enter a prompt like "A cat wearing a wizard hat"
3. Connect output to Preview Image node

### Batch Image Generation
1. Add "Nano Banana Gemini" node
2. Set batch_size to 4
3. Enter your prompt
4. Get 4 variations generated concurrently with progress tracking

### Image-to-Image
1. Load an image
2. Connect to "images" input of Gemini node
3. Add prompt describing desired changes
4. Model will use the image as context

### Combining Multiple Images
1. Add "Batch Images" node
2. Connect images from different sources
3. The node automatically creates new inputs as you connect
4. All images are resized and combined into a single batch
5. Use the batch for further processing or saving

## Development

### Project Structure
```
comfy_nanobanana/
├── src/comfy_nanobanana/
│   ├── __init__.py
│   ├── nodes.py          # ComfyUI node implementations
│   └── gemini_api.py     # Gemini API client with async support
├── web/
│   ├── index.js          # Extension entry point
│   └── node/
│       ├── batch_images_dynamic.js  # Dynamic input handling for Batch Images
│       └── gemini_api_key_mask.js   # API key masking and secure export handling
├── requirements.txt
└── pyproject.toml
```

### Dev Setup
```bash
cd comfy_nanobanana
pip install -e .[dev]
pre-commit install
```

### Developer Notes

#### API Key Security Implementation
The node implements a dual-mode export system:
- **UI Masking**: API keys are visually masked in the interface (showing only first 4 and last 2 characters)
- **Workflow Export**: Automatically strips API keys for safe sharing
- **API Export**: Preserves API keys for programmatic use (requires Developer Mode)

This design balances security with developer convenience, ensuring users don't accidentally expose credentials while maintaining ease of deployment for production systems.

## Troubleshooting

### Common Issues

**"No API key provided"**
- Ensure `GEMINI_API_KEY` is set or enter key in node

**"Seed must be between 0 and 2147483647"**
- Gemini API requires 32-bit integer seeds

**Unexpected empty image output**
- Verify you selected one of the supported Gemini image models
- If the API returns no image payload, the node falls back to a placeholder image to avoid crashing the workflow

## Contributing

Pull requests welcome! Please:
1. Follow existing code style
2. Add tests for new features
3. Update documentation

## License

MIT License - see [LICENSE](LICENSE) file

## Credits

Created with [ComfyUI Extension Template](https://github.com/Comfy-Org/cookiecutter-comfy-extension)
