/**
 * File: core_help.js
 * Project: Jovimetrix
 * code based on mtb nodes by Mel Massadian https://github.com/melMass/comfy_mtb/
 */

import { app } from '../../../scripts/app.js'
import { nodeCleanup } from '../util/util_node.js'
import '../extern/shodown.min.js'

const JOV_WEBWIKI_URL = "https://github.com/Amorano/Jovimetrix/wiki";
// const JOV_HELP_URL = "https://raw.githubusercontent.com/Amorano/Jovimetrix-examples/master/node";
const CACHE_DOCUMENTATION = {};

if (!window.jovimetrixEvents) {
    window.jovimetrixEvents = new EventTarget();
}
const jovimetrixEvents = window.jovimetrixEvents;

const new_menu = app.ui.settings.getSettingValue("Comfy.UseNewMenu", "Disabled");

const documentationConverter = new showdown.Converter({
    tables: true,
    strikethrough: true,
    emoji: true,
    ghCodeBlocks: true,
    tasklists: true,
    ghMentions: true,
    smoothLivePreview: true,
    simplifiedAutoLink: true,
    parseImgDimensions: true,
    openLinksInNewWindow: true,
});

const JOV_HELP_URL = "/jovimetrix/doc";

async function load_help(name, custom_data) {
    // overwrite
    if (custom_data) {
        CACHE_DOCUMENTATION[name] = documentationConverter.makeHtml(custom_data);
    }

    if (name in CACHE_DOCUMENTATION) {
        return CACHE_DOCUMENTATION[name];
    }

    const url = `${JOV_HELP_URL}/${name}`;
    // Check if data is already cached
    const result = fetch(url,
        { cache: "no-store" }
    )
        .then(response => {
            if (!response.ok) {
                return `Failed to load documentation: ${name}\n\n${response}`
            }
            return response.text();
        })
        .then(data => {
            // Cache the fetched data
            if (data.startsWith("unknown")) {
                data = `
                    <div align="center">
                        <h3>${data}</h3>
                        <h4>SELECT A NODE TO SEE HELP</h4>
                        <h4>JOVIMETRIX 🔺🟩🔵 NODES ALL HAVE HELP</h4>
                    </div>
                `;
            };
            CACHE_DOCUMENTATION[name] = data;
            return CACHE_DOCUMENTATION[name];
        })
        .catch(error => {
            console.error('Error:', error);
            return `Failed to load documentation: ${name}\n\n${error}`
        });
    return result;
}

app.registerExtension({
    name: "jovimetrix.help",
    setup() {
        if(app?.extensionManager) {
            const onSelectionChange = app.canvas.onSelectionChange;
            app.canvas.onSelectionChange = function(selectedNodes) {
                const me = onSelectionChange?.apply(this);
                if (selectedNodes && Object.keys(selectedNodes).length > 0) {
                    const firstNodeKey = Object.keys(selectedNodes)[0];
                    const firstNode = selectedNodes[firstNodeKey];
                    const data = {
                        class: firstNode?.getNickname() || "unknown",
                        name: firstNode.type
                    }
                    const event = new CustomEvent('jovimetrixHelpRequested', { detail: data });
                    jovimetrixEvents.dispatchEvent(event);
                }
                return me;
            }
        }
    },
	async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!nodeData?.category?.startsWith("JOVIMETRIX")) {
            return;
        }

        // MENU HELP!
        const getExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (_, options) {
            const me = getExtraMenuOptions?.apply(this, arguments);
            if (!this.title.endsWith('🧙🏽‍♀️')) {
                const widget_tooltip = (this.widgets || [])
                    .find(widget => widget.type === 'JTOOLTIP');
                if (widget_tooltip) {
                    const tips = widget_tooltip.options.default || {};
                    const url = tips['_'];
                    const help_menu = [{
                        content: `HELP: ${this.title}`,
                        callback: () => {
                            LiteGraph.closeAllContextMenus();
                            window.open(`${JOV_WEBWIKI_URL}/${url}`, '_blank');
                            this.setDirtyCanvas(true, true);
                        }
                    }];
                    if (help_menu.length) {
                        options.push(...help_menu, null);
                    }
                }
            }
            return me;
        }

        // if the old menu is present....
        if(new_menu == "Disabled" || !app.extensionManager) {
            let opts = { icon_size: 14, icon_margin: 3 }
            const iconSize = opts.icon_size ? opts.icon_size : 14;
            const iconMargin = opts.icon_margin ? opts.icon_margin : 3;
            let docElement = null;
            let contentWrapper = null;

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = async function () {
                const me = onNodeCreated?.apply(this);
                this.offsetX = 0;
                this.offsetY = 0;
                this.show_doc = false;
                this.onRemoved = function () {
                    nodeCleanup(this);
                    if (docElement) {
                        docElement.remove();
                        docElement = null;
                    }
                    if (contentWrapper) {
                        contentWrapper.remove();
                        contentWrapper = null;
                    }
                }
                return me;
            }

            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = async function (ctx) {
                const me = onDrawForeground?.apply?.(this, arguments);
                if (this.flags.collapsed) return me;

                const x = this.size[0] - iconSize - iconMargin
                if (this.show_doc && docElement === null) {

                    docElement = document.createElement('div')
                    docElement.classList.add('jov-panel-doc-popup');

                    const widget_tooltip = (this.widgets || [])
                        .find(widget => widget.type === 'JTOOLTIP');

                    if (widget_tooltip) {
                        const tips = widget_tooltip.options.default || {};
                        const url_name = `jovimetrix/${tips['*']}`;
                        docElement.innerHTML = await load_help(url_name);
                    }

                    // resize handle
                    const resizeHandle = document.createElement('div');
                    resizeHandle.style.width = '0';
                    resizeHandle.style.height = '0';
                    resizeHandle.style.position = 'absolute';
                    resizeHandle.style.bottom = '0';
                    resizeHandle.style.right = '0';
                    resizeHandle.style.cursor = 'se-resize';
                    const borderColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim();

                    resizeHandle.style.borderTop = '5px solid transparent';
                    resizeHandle.style.borderLeft = '5px solid transparent';
                    resizeHandle.style.borderBottom = `5px solid ${borderColor}`;
                    resizeHandle.style.borderRight = `5px solid ${borderColor}`;
                    docElement.appendChild(resizeHandle);
                    let isResizing = false;
                    let startX, startY, startWidth, startHeight;

                    resizeHandle.addEventListener('mousedown', function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            isResizing = true;
                            startX = e.clientX;
                            startY = e.clientY;
                            startWidth = parseInt(document.defaultView.getComputedStyle(docElement).width, 10);
                            startHeight = parseInt(document.defaultView.getComputedStyle(docElement).height, 10);
                        },
                        { signal: this.helpClose.signal },
                    );

                    const buttons = document.createElement('div');
                    // wiki page
                    const wikiButton = document.createElement('div');
                    wikiButton.textContent = '🌐';
                    wikiButton.style.position = 'absolute';
                    wikiButton.style.top = '6px';
                    wikiButton.style.right = '22px';
                    wikiButton.style.cursor = 'pointer';
                    wikiButton.style.padding = '4px';
                    wikiButton.style.font = 'bold 14px monospace';
                    wikiButton.addEventListener('mousedown', (e) => {
                        e.stopPropagation();
                        const widget_tooltip = (this.widgets || [])
                            .find(widget => widget.type === 'JTOOLTIP');
                        if (widget_tooltip) {
                            const tips = widget_tooltip.options.default || {};
                            const url = tips['_'];
                            if (url !== undefined) {
                                window.open(`${JOV_WEBWIKI_URL}/${url}`, '_blank');
                            }
                            wikiButton.tooltip = `WIKI PAGE: ${url}`
                        }
                    });
                    buttons.appendChild(wikiButton);

                    // close button
                    const closeButton = document.createElement('div');
                    closeButton.textContent = '❌';
                    closeButton.style.position = 'absolute';
                    closeButton.style.top = '6px';
                    closeButton.style.right = '4px';
                    closeButton.style.cursor = 'pointer';
                    closeButton.style.padding = '4px';
                    closeButton.style.font = 'bold 14px monospace';
                    closeButton.addEventListener('mousedown', (e) => {
                            e.stopPropagation();
                            this.show_doc = !this.show_doc
                            if (contentWrapper) {
                                contentWrapper.remove()
                                contentWrapper = null
                            }
                            docElement.parentNode.removeChild(docElement)
                            docElement = null
                        },
                        { signal: this.helpClose.signal },
                    );
                    buttons.appendChild(closeButton);
                    docElement.appendChild(buttons);

                    document.addEventListener('mousemove', function (e) {
                            if (!isResizing) return;
                            const scale = app.canvas.ds.scale;
                            const newWidth = startWidth + (e.clientX - startX) / scale;
                            const newHeight = startHeight + (e.clientY - startY) / scale;;
                            docElement.style.width = `${newWidth}px`;
                            docElement.style.height = `${newHeight}px`;
                        },
                        { signal: this.helpClose.signal },
                    );
                    document.addEventListener('mouseup', function () {
                            isResizing = false
                        },
                        { signal: this.helpClose.signal },
                    );
                    document.body.appendChild(docElement);
                } else if (!this.show_doc && docElement !== null) {
                    docElement.parentNode?.removeChild(docElement)
                    docElement = null;
                }

                if (this.show_doc && docElement !== null) {
                    const rect = ctx.canvas.getBoundingClientRect()
                    const scaleX = rect.width / ctx.canvas.width
                    const scaleY = rect.height / ctx.canvas.height
                    const transform = new DOMMatrix()
                        .scaleSelf(scaleX, scaleY)
                        .multiplySelf(ctx.getTransform())
                        .translateSelf(this.size[0] * scaleX * Math.max(1.0,window.devicePixelRatio) , 0)
                        .translateSelf(10, -32)

                    const scale = new DOMMatrix()
                        .scaleSelf(transform.a, transform.d);

                    const styleObject = {
                        transformOrigin: '0 0',
                        transform: scale,
                        left: `${transform.a + transform.e}px`,
                        top: `${transform.d + transform.f}px`,
                    };
                    Object.assign(docElement.style, styleObject);
                }

                ctx.save();
                ctx.translate(x-3, -LiteGraph.NODE_TITLE_HEIGHT * 0.65);
                ctx.scale(iconSize / 32, iconSize / 32);
                ctx.font = `bold ${LiteGraph.NODE_TITLE_HEIGHT * 1.35}px monospace`;
                ctx.fillText('🛈', 0, 24); // ℹ️
                ctx.restore()
                return me;
            }

            // ? clicked
            const mouseDown = nodeType.prototype.onMouseDown
            nodeType.prototype.onMouseDown = function (e, localPos) {
                const r = mouseDown ? mouseDown.apply(this, arguments) : undefined
                const iconX = this.size[0] - iconSize - iconMargin
                const iconY = iconSize - 34
                if (
                    localPos[0] > iconX &&
                    localPos[0] < iconX + iconSize &&
                    localPos[1] > iconY &&
                    localPos[1] < iconY + iconSize
                ) {
                    // Pencil icon was clicked, open the editor
                    // this.openEditorDialog();
                    if (this.show_doc === undefined) {
                        this.show_doc = true;
                    } else {
                        this.show_doc = !this.show_doc;
                    }
                    if (this.show_doc) {
                        this.helpClose = new AbortController()
                    } else {
                        this.helpClose.abort()
                    }
                    // Dispatch a custom event with the node name
                    const data = {
                        class: this.getNickname() || "jovimetrix",
                        name: this.type
                    }
                    const event = new CustomEvent('jovimetrixHelpRequested', { detail: data });
                    jovimetrixEvents.dispatchEvent(event);
                    return true;
                }
                return r;
            }
        }
	}
})

let HELP_PANEL_CONTENT = `
<div align="center">
    <h4>SELECT A NODE TO SEE HELP</h4>
    <h4>JOVIMETRIX 🔺🟩🔵 NODES ALL HAVE HELP</h4>
</div>
`;

if(new_menu != "Disabled" && app.extensionManager) {
    let sidebarElement;

    const updateContent = async (node, data) => {
        if (sidebarElement) {
            HELP_PANEL_CONTENT = await load_help(node, data);
            sidebarElement.innerHTML = HELP_PANEL_CONTENT;
        }
    };

    app.extensionManager.registerSidebarTab({
        id: "jovimetrix.sidebar.help",
        icon: "pi pi-money-bill",
        title: "Jovimetrix Lore",
        tooltip: "The Akashic records for all things JOVIMETRIX 🔺🟩🔵",
        type: "custom",
        render: async (el) => {
            sidebarElement = el;
            el.innerHTML = "<div>Loading...</div>";
            await updateContent('_', HELP_PANEL_CONTENT);
        }
    });

    // Listen for the custom event
    jovimetrixEvents.addEventListener('jovimetrixHelpRequested', async (event) => {
        const node = `${event.detail.class}/${event.detail.name}`;
        await updateContent(node);
    });
}

