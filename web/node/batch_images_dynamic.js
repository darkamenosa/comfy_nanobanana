import { app } from "/scripts/app.js";

const TypeSlot = {
    Input: 1,
    Output: 2,
};

const TypeSlotEvent = {
    Connect: true,
    Disconnect: false,
};

const _ID = "BatchImages";
const _PREFIX = "image";
const _TYPE = "IMAGE";

app.registerExtension({
    name: "comfy_nanobanana.batch_images_dynamic",
    async beforeRegisterNodeDef(nodeType, nodeData, appRef) {
        if (!nodeData || nodeData.name !== _ID) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const me = onNodeCreated?.apply(this);
            // Only add a starter input if none exist (fresh node, not from load)
            const hasImageInput = (this.inputs || []).some((i) => i && i.type === _TYPE);
            if (!hasImageInput) {
                this.addInput(_PREFIX, _TYPE);
                const slot = this.inputs[this.inputs.length - 1];
                if (slot) slot.color_off = "#666";
            }
            return me;
        };

        // Ensure correct number of inputs when loading from a saved workflow
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const me = onConfigure?.apply(this, arguments);
            try {
                const savedInputs = Array.isArray(info?.inputs) ? info.inputs : [];
                const desiredCount = savedInputs.filter((inp) => inp && inp.type === _TYPE && String(inp.name || "").startsWith(_PREFIX)).length;
                const currentCount = (this.inputs || []).filter((i) => i && i.type === _TYPE).length;
                // Add missing image inputs to match saved connections
                for (let i = currentCount; i < desiredCount; i++) {
                    this.addInput(`${_PREFIX}${i + 1}`, _TYPE);
                    const slot = this.inputs[this.inputs.length - 1];
                    if (slot) slot.color_off = "#666";
                }
                // Always keep one empty input at the end
                let last = this.inputs[this.inputs.length - 1];
                if (last === undefined || last.type !== _TYPE || last.link !== null) {
                    this.addInput(_PREFIX, _TYPE);
                    last = this.inputs[this.inputs.length - 1];
                    if (last) last.color_off = "#666";
                }
            } catch (e) {
                // no-op
            }
            return me;
        };

        const onConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function (slotType, slot_idx, event, link_info, node_slot) {
            const me = onConnectionsChange?.apply(this, arguments);

            if (slotType === TypeSlot.Input) {
                if (link_info && event === TypeSlotEvent.Connect) {
                    const fromNode = this.graph._nodes.find((other) => other.id == link_info.origin_id);
                    if (fromNode) {
                        const parent_link = fromNode.outputs[link_info.origin_slot];
                        if (parent_link) {
                            node_slot.type = parent_link.type;
                            node_slot.name = `${_PREFIX}_`;
                        }
                    }
                } else if (event === TypeSlotEvent.Disconnect) {
                    try { this.removeInput(slot_idx); } catch (e) {}
                }

                // Reindex and prune empties
                // Rename only connected inputs; leave empties as 'image'
                let slot_tracker = {};
                for (let i = 0; i < this.inputs.length; i++) {
                    const slot = this.inputs[i];
                    if (!slot || slot.type !== _TYPE) continue;
                    if (slot.link == null) {
                        slot.name = _PREFIX;
                        continue;
                    }
                    // Normalize base name to plain prefix (strip trailing digits and underscores)
                    let base = (slot.name || _PREFIX);
                    base = base.replace(/[0-9]+$/g, "");
                    base = base.replace(/_$/g, "");
                    if (!base) base = _PREFIX;
                    const count = (slot_tracker[base] || 0) + 1;
                    slot_tracker[base] = count;
                    // Display without underscore: image1, image2, ...
                    slot.name = `${base}${count}`;
                }

                // Ensure exactly one trailing empty IMAGE input
                let lastConnected = -1;
                for (let i = 0; i < this.inputs.length; i++) {
                    const inp = this.inputs[i];
                    if (inp && inp.type === _TYPE && inp.link != null) lastConnected = i;
                }
                // Remove extra empties beyond one after the last connected
                let emptyAfter = 0;
                for (let i = this.inputs.length - 1; i >= 0; i--) {
                    const inp = this.inputs[i];
                    if (!inp || inp.type !== _TYPE) continue;
                    const isEmpty = inp.link == null;
                    if (i > lastConnected && isEmpty) {
                        emptyAfter += 1;
                        if (emptyAfter > 1) this.removeInput(i);
                    }
                }
                let last = this.inputs[this.inputs.length - 1];
                if (last === undefined || last.type !== _TYPE || last.link !== null) {
                    this.addInput(_PREFIX, _TYPE);
                    last = this.inputs[this.inputs.length - 1];
                    if (last) last.color_off = "#666";
                }

                this?.graph?.setDirtyCanvas(true);
                return me;
            }

            return me;
        };

        return nodeType;
    },
});
