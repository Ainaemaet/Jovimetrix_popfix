/**
 * File: colorize.js
 * Project: Jovimetrix
 *
 */

import { app } from "../../../scripts/app.js";
import { $el } from "../../../scripts/ui.js";
import { jovimetrix } from "./jovimetrix.js";

const ext = {
    name: "jovimetrix.colorize",

    async init() {
		const showButton = $el("button.comfy-settings-btn", {
			textContent: "🎨",
			style: {
				left: "15px",
				cursor: "pointer",
				display: "unset",
			},
		});

		showButton.onclick = () => {
            jovimetrix.config.show();
		};
		document.querySelector(".comfy-settings-btn").after(showButton);
	},

    async beforeRegisterNodeDef(nodeType, nodeData) {
        const node = jovimetrix.node_color_get(nodeData.name);
        if (node) {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                //console.info(nodeData.name, node);
                if (nodeData.color === undefined) {
                    this['color'] = (node.title || "#7F7F7FEE")
                }

                if (nodeData.bgcolor === undefined) {
                    this['bgcolor'] = (node.body || "#7F7F7FEE")
                }
                /*
                // default, box, round, card
                if (nodeData.shape === undefined || nodeData.shape == false) {
                    this['_shape'] = nodeData._shape ? nodeData._shape : found.shape ?
                    found.shape in ['default', 'box', 'round', 'card'] : 'round';
                }*/
                // console.info("jovi-colorized", this.title, this.color, this.bgcolor, this._shape);
                // result.serialize_widgets = true
                return result;
            }
        }
    }
}

app.registerExtension(ext);
