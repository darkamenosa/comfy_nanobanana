import { app } from "/scripts/app.js";

const GEMINI_NODE_NAME = "NanoBananaGeminiImageNode";
const API_KEY_WIDGET_NAME = "api_key";

app.registerExtension({
    name: "comfy_nanobanana.gemini_api_key_mask",
    
    async beforeRegisterNodeDef(nodeType, nodeData, appRef) {
        if (!nodeData || nodeData.name !== GEMINI_NODE_NAME) return;

        // Store original onNodeCreated
        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        
        // Override onNodeCreated
        nodeType.prototype.onNodeCreated = function() {
            // Call original first
            if (origOnNodeCreated) {
                origOnNodeCreated.apply(this, arguments);
            }
            
            // Get reference to this node
            const node = this;
            
            // Find the api_key widget after a small delay to ensure it's initialized
            requestAnimationFrame(() => {
                const apiKeyWidget = node.widgets?.find(w => w.name === API_KEY_WIDGET_NAME);
                if (!apiKeyWidget) {
                    console.log("[NanoBanana] API key widget not found");
                    return;
                }
                console.log("[NanoBanana] Setting up API key masking for widget:", apiKeyWidget);
                
                // Store the actual API key value
                let actualApiKey = apiKeyWidget.value || "";
                let isShowingReal = false;
                
                // Helper function to mask the API key
                function maskApiKey(key) {
                    if (!key || key.length === 0) return "";
                    if (key.includes("*")) return key; // Already masked
                    
                    // For short keys, mask everything
                    if (key.length <= 6) {
                        return "*".repeat(key.length);
                    }
                    
                    // Show first 4 and last 2 characters
                    const firstPart = key.substring(0, 4);
                    const lastPart = key.substring(key.length - 2);
                    const maskLength = Math.max(10, key.length - 6);
                    
                    return firstPart + "*".repeat(maskLength) + lastPart;
                }
                
                // Store the original callback
                const origCallback = apiKeyWidget.callback;
                
                // Override the callback to capture real value
                apiKeyWidget.callback = function(v) {
                    // Skip if the value is masked (contains asterisks)
                    if (v && v.includes("*") && actualApiKey) {
                        // Don't update with masked value
                        this.value = isShowingReal ? actualApiKey : maskApiKey(actualApiKey);
                        return;
                    }
                    
                    // Store the actual value
                    actualApiKey = v || "";
                    
                    // Call original callback if it exists
                    if (origCallback) {
                        origCallback.call(this, v);
                    }
                    
                    // Update display
                    if (!isShowingReal) {
                        this.value = maskApiKey(actualApiKey);
                    }
                };
                
                // If there's already a value, mask it
                if (apiKeyWidget.value && !apiKeyWidget.value.includes("*")) {
                    actualApiKey = apiKeyWidget.value;
                    apiKeyWidget.value = maskApiKey(actualApiKey);
                }
                
                // Store actual value getter for serialization
                apiKeyWidget.getActualValue = function() {
                    return actualApiKey;
                };
                
                // Override serialization - keep API key for API format
                apiKeyWidget.serializeValue = function() {
                    // Return actual API key for API format (used programmatically)
                    return actualApiKey;
                };
                
                // Override computeSize to ensure the widget value is used correctly
                const origComputeSize = apiKeyWidget.computeSize;
                if (origComputeSize) {
                    apiKeyWidget.computeSize = function(width) {
                        // Temporarily store the display value
                        const tempVal = this.value;
                        // Use actual value for computation
                        this.value = actualApiKey;
                        const result = origComputeSize.call(this, width);
                        // Restore display value
                        this.value = tempVal;
                        return result;
                    };
                }
                
                console.log("[NanoBanana] API key masking setup complete");
            });
        };
        
        // Override onSerialize to EXCLUDE API key from exports
        const origOnSerialize = nodeType.prototype.onSerialize;
        nodeType.prototype.onSerialize = function(o) {
            if (origOnSerialize) {
                origOnSerialize.call(this, o);
            }
            
            // Find api_key widget and REMOVE it from export
            const apiKeyWidget = this.widgets?.find(w => w.name === API_KEY_WIDGET_NAME);
            if (apiKeyWidget) {
                const widgetIdx = this.widgets.indexOf(apiKeyWidget);
                if (widgetIdx >= 0 && o.widgets_values) {
                    // Set to empty string instead of actual value for security
                    o.widgets_values[widgetIdx] = "";
                    console.log("[NanoBanana] API key excluded from workflow export for security");
                }
            }
        };
        
        // Override onConfigure to handle loading
        const origOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function(o) {
            if (origOnConfigure) {
                origOnConfigure.call(this, o);
            }
            
            // After configuration, handle API key if present
            requestAnimationFrame(() => {
                const apiKeyWidget = this.widgets?.find(w => w.name === API_KEY_WIDGET_NAME);
                if (apiKeyWidget && o.widgets_values) {
                    const widgetIdx = this.widgets.indexOf(apiKeyWidget);
                    if (widgetIdx >= 0) {
                        const value = o.widgets_values[widgetIdx];
                        if (value && value !== "" && !value.includes("*")) {
                            // This is a real API key from an old workflow, store it and mask display
                            if (apiKeyWidget.getActualValue) {
                                apiKeyWidget.callback(value);
                            } else {
                                apiKeyWidget.value = value;
                            }
                            console.log("[NanoBanana] Loaded API key from workflow (consider re-saving to exclude it)");
                        } else if (!value || value === "") {
                            // No API key in workflow (expected for new secure exports)
                            console.log("[NanoBanana] No API key in workflow - please enter it manually or use GEMINI_API_KEY env variable");
                        }
                    }
                }
            });
        };
        
        return nodeType;
    }
});