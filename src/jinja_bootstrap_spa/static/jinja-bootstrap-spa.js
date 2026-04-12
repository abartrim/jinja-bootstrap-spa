export const JBS_HEADERS = {
    accept: "text/html",
    marker: "X-JBS-Request",
    component: "X-JBS-Component",
    action: "X-JBS-Action",
};
export const JBS_ACTIONS = {
    filter: "filter",
    page: "page",
    refresh: "refresh",
    row: "row",
    sort: "sort",
};
export const JBS_PERSISTENCE = {
    memory: "memory",
    querystring: "querystring",
    session: "session",
};
export const JBS_STREAM_EVENTS = {
    refresh: "refresh",
};
const DEFAULT_TABLE_STATE_KEYS = ["page", "page_size", "sort_by", "sort_dir", "query"];
const TRANSIENT_STATE_KEYS = new Set(["row_id", "intent"]);
function cloneState(state) {
    return structuredClone(state);
}
function parseState(value) {
    if (!value) {
        return {};
    }
    try {
        const parsed = JSON.parse(value);
        return parsed ?? {};
    }
    catch {
        return {};
    }
}
function normalizeFormData(form) {
    const nextState = {};
    const formData = new FormData(form);
    for (const [key, rawValue] of formData.entries()) {
        const value = typeof rawValue === "string" ? rawValue : rawValue.name;
        const existing = nextState[key];
        if (existing === undefined) {
            nextState[key] = value;
            continue;
        }
        nextState[key] = Array.isArray(existing) ? [...existing, value] : [existing, value];
    }
    return nextState;
}
function applyStatePatch(current, patch) {
    return { ...current, ...patch };
}
function stripTransientState(state) {
    const nextState = cloneState(state);
    for (const key of TRANSIENT_STATE_KEYS) {
        delete nextState[key];
    }
    return nextState;
}
function appendStateParams(url, state) {
    for (const [key, value] of Object.entries(state)) {
        url.searchParams.delete(key);
        if (value === null) {
            continue;
        }
        if (Array.isArray(value)) {
            for (const item of value) {
                url.searchParams.append(key, String(item));
            }
            continue;
        }
        url.searchParams.set(key, String(value));
    }
}
function readStateKeys(component) {
    const raw = component.dataset.jbsStateKeys;
    if (!raw) {
        return DEFAULT_TABLE_STATE_KEYS;
    }
    return raw
        .split(",")
        .map((key) => key.trim())
        .filter(Boolean);
}
function readQueryState(component) {
    const params = new URLSearchParams(window.location.search);
    const nextState = {};
    for (const key of readStateKeys(component)) {
        const values = params.getAll(key);
        if (values.length === 0) {
            continue;
        }
        nextState[key] = values.length === 1 ? values[0] : values;
    }
    return nextState;
}
function sessionStorageKey(component, key) {
    return `jbs:${component.dataset.jbsComponent ?? "component"}:${key}`;
}
function parseStreamPayload(data) {
    if (!data) {
        return {};
    }
    try {
        return JSON.parse(data);
    }
    catch {
        return {};
    }
}
export class JBSRuntime {
    constructor(options = {}) {
        this.stateStore = new Map();
        this.streamStore = new Map();
        this.autocompleteTimers = new Map();
        this.autocompleteRequests = new Map();
        this.overlayReturnFocus = new Map();
        this.initialized = false;
        this.handleClick = async (event) => {
            const target = event.target;
            const statusDismiss = target?.closest("[data-jbs-status-dismiss]");
            if (statusDismiss) {
                event.preventDefault();
                statusDismiss.closest("[data-jbs-status-region]")?.remove();
                return;
            }
            const overlayOpen = target?.closest("[data-jbs-overlay-open]");
            if (overlayOpen) {
                const overlayId = overlayOpen.dataset.jbsOverlayOpen;
                const overlay = overlayId ? document.getElementById(overlayId) : null;
                if (overlay) {
                    event.preventDefault();
                    this.openOverlay(overlay, overlayOpen);
                }
                return;
            }
            const overlayClose = target?.closest("[data-jbs-overlay-close]");
            if (overlayClose) {
                const overlay = overlayClose.closest("[data-jbs-overlay]");
                if (overlay) {
                    event.preventDefault();
                    this.closeOverlay(overlay);
                }
                return;
            }
            if (target instanceof HTMLElement && target.matches("[data-jbs-overlay]")) {
                event.preventDefault();
                this.closeOverlay(target);
                return;
            }
            const autocompleteOption = target?.closest("[data-jbs-autocomplete-option]");
            if (autocompleteOption) {
                event.preventDefault();
                this.selectAutocompleteOption(autocompleteOption);
                return;
            }
            const menuTrigger = target?.closest("[data-jbs-menu-trigger]");
            if (menuTrigger) {
                const menu = menuTrigger.closest("[data-jbs-menu]");
                if (!menu) {
                    return;
                }
                event.preventDefault();
                this.toggleMenu(menu);
                return;
            }
            const menuItem = target?.closest("[data-jbs-menu] [role='menuitem']");
            if (menuItem) {
                const menu = menuItem.closest("[data-jbs-menu]");
                if (menuItem.matches(".disabled, [disabled]")) {
                    event.preventDefault();
                    this.closeMenu(menu ?? menuItem);
                    return;
                }
                if (menu) {
                    this.closeMenu(menu);
                }
            }
            else if (!target?.closest("[data-jbs-menu]")) {
                this.closeAllMenus();
            }
            if (!target?.closest("[data-jbs-autocomplete]")) {
                this.closeAllAutocompletes();
            }
            const trigger = target?.closest("[data-jbs-action]");
            if (!trigger) {
                return;
            }
            const component = this.findComponent(trigger);
            if (!component) {
                return;
            }
            event.preventDefault();
            const action = trigger.dataset.jbsAction ?? "refresh";
            const patch = this.buildPatchFromTrigger(component, trigger, action);
            await this.requestComponent(component, action, patch, trigger);
        };
        this.handleInput = (event) => {
            const input = event.target instanceof HTMLInputElement ? event.target : null;
            if (!input?.hasAttribute("data-jbs-autocomplete-input")) {
                return;
            }
            const wrapper = input.closest("[data-jbs-autocomplete]");
            if (!wrapper) {
                return;
            }
            const { value } = this.autocompleteElements(wrapper);
            if (value && input.value !== (value.dataset.jbsAutocompleteSelectedLabel ?? "")) {
                value.value = "";
            }
            const key = this.autocompleteKey(wrapper);
            const existingTimer = this.autocompleteTimers.get(key);
            if (existingTimer !== undefined) {
                window.clearTimeout(existingTimer);
            }
            const timer = window.setTimeout(() => {
                void this.requestAutocompleteOptions(wrapper, input.value);
            }, 150);
            this.autocompleteTimers.set(key, timer);
        };
        this.handleKeydown = (event) => {
            const target = event.target;
            const autocompleteInput = target?.closest("[data-jbs-autocomplete-input]");
            const autocompleteOption = target?.closest("[data-jbs-autocomplete-option]");
            if (autocompleteInput instanceof HTMLInputElement) {
                const wrapper = autocompleteInput.closest("[data-jbs-autocomplete]");
                const panel = wrapper?.querySelector("[data-jbs-autocomplete-panel]");
                if (!wrapper || !panel) {
                    return;
                }
                if (event.key === "ArrowDown") {
                    event.preventDefault();
                    this.focusAutocompleteOption(panel, 1);
                    return;
                }
                if (event.key === "Escape") {
                    this.closeAutocomplete(wrapper);
                    return;
                }
            }
            if (autocompleteOption instanceof HTMLElement) {
                const wrapper = autocompleteOption.closest("[data-jbs-autocomplete]");
                const panel = wrapper?.querySelector("[data-jbs-autocomplete-panel]");
                if (!wrapper || !panel) {
                    return;
                }
                if (event.key === "ArrowDown") {
                    event.preventDefault();
                    this.focusAutocompleteOption(panel, 1);
                    return;
                }
                if (event.key === "ArrowUp") {
                    event.preventDefault();
                    this.focusAutocompleteOption(panel, -1);
                    return;
                }
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    this.selectAutocompleteOption(autocompleteOption);
                    return;
                }
                if (event.key === "Escape") {
                    event.preventDefault();
                    this.closeAutocomplete(wrapper);
                    const input = wrapper.querySelector("[data-jbs-autocomplete-input]");
                    input?.focus();
                    return;
                }
            }
            if (event.key === "Escape") {
                if (this.closeTopmostOverlay()) {
                    return;
                }
                this.closeAllAutocompletes();
                this.closeAllMenus();
            }
        };
        this.handleSubmit = async (event) => {
            const form = event.target instanceof HTMLFormElement ? event.target : null;
            if (!form || !form.hasAttribute("data-jbs-form")) {
                return;
            }
            const component = this.findComponent(form);
            if (!component) {
                return;
            }
            event.preventDefault();
            const patch = normalizeFormData(form);
            const nextState = applyStatePatch(this.getState(component), patch);
            nextState.page = 1;
            await this.requestComponent(component, JBS_ACTIONS.filter, nextState, form);
        };
        this.fetchImpl =
            options.fetchImpl ?? ((input, init) => window.fetch(input, init));
    }
    init() {
        if (this.initialized) {
            return;
        }
        document.addEventListener("click", this.handleClick);
        document.addEventListener("input", this.handleInput);
        document.addEventListener("keydown", this.handleKeydown);
        document.addEventListener("submit", this.handleSubmit);
        this.hydrate(document);
        this.initialized = true;
    }
    hydrate(root) {
        const components = root.querySelectorAll("[data-jbs-component][data-jbs-endpoint]");
        for (const component of components) {
            const key = this.componentKey(component);
            const state = this.hydratedState(component, key);
            component.dataset.jbsState = JSON.stringify(state);
            this.stateStore.set(key, state);
            this.connectStream(component, key);
        }
    }
    getState(component) {
        const key = this.componentKey(component);
        const current = this.stateStore.get(key);
        if (current) {
            return cloneState(current);
        }
        const state = parseState(component.dataset.jbsState ?? null);
        this.stateStore.set(key, state);
        return cloneState(state);
    }
    async refresh(componentOrId, patch = {}) {
        const component = this.resolveComponent(componentOrId);
        if (!component) {
            throw new Error("Unable to resolve component to refresh.");
        }
        await this.requestComponent(component, JBS_ACTIONS.refresh, applyStatePatch(this.getState(component), patch), null);
    }
    resolveComponent(componentOrId) {
        if (typeof componentOrId !== "string") {
            return componentOrId;
        }
        return document.getElementById(componentOrId);
    }
    componentKey(component) {
        return (component.dataset.jbsKey ??
            component.id ??
            component.dataset.jbsEndpoint ??
            "jbs-component");
    }
    hydratedState(component, key) {
        const baseState = parseState(component.dataset.jbsState ?? null);
        const persist = this.persistStrategy(component);
        if (persist === JBS_PERSISTENCE.querystring) {
            return stripTransientState(applyStatePatch(baseState, readQueryState(component)));
        }
        if (persist === JBS_PERSISTENCE.session && typeof sessionStorage !== "undefined") {
            const saved = sessionStorage.getItem(sessionStorageKey(component, key));
            return stripTransientState(applyStatePatch(baseState, parseState(saved)));
        }
        return stripTransientState(baseState);
    }
    persistStrategy(component) {
        const persist = component.dataset.jbsPersist;
        if (persist === JBS_PERSISTENCE.querystring ||
            persist === JBS_PERSISTENCE.session) {
            return persist;
        }
        return JBS_PERSISTENCE.memory;
    }
    persistState(component, key, state) {
        const persist = this.persistStrategy(component);
        if (persist === JBS_PERSISTENCE.querystring) {
            const url = new URL(window.location.href);
            const keys = readStateKeys(component);
            for (const stateKey of keys) {
                url.searchParams.delete(stateKey);
            }
            appendStateParams(url, Object.fromEntries(keys.map((stateKey) => [stateKey, state[stateKey] ?? null])));
            window.history.replaceState(window.history.state, "", url);
            return;
        }
        if (persist === JBS_PERSISTENCE.session && typeof sessionStorage !== "undefined") {
            sessionStorage.setItem(sessionStorageKey(component, key), JSON.stringify(state));
        }
    }
    connectStream(component, key) {
        const endpoint = component.dataset.jbsSse;
        const eventName = component.dataset.jbsSseEvent ?? JBS_STREAM_EVENTS.refresh;
        const existing = this.streamStore.get(key);
        if (!endpoint) {
            existing?.close();
            this.streamStore.delete(key);
            return;
        }
        if (existing?.url === new URL(endpoint, window.location.href).toString()) {
            return;
        }
        existing?.close();
        const stream = new EventSource(endpoint);
        const onMessage = async (event) => {
            const current = document.getElementById(component.id || key);
            if (!current) {
                return;
            }
            const payload = parseStreamPayload(event.data);
            const target = payload.target;
            if (target && target !== current.id && target !== key) {
                return;
            }
            const nextState = applyStatePatch(this.getState(current), payload.patch ?? {});
            const detail = {
                component: current,
                key,
                endpoint,
                event: eventName,
                data: event.data,
            };
            current.dispatchEvent(new CustomEvent("jbs:stream-event", { detail }));
            await this.requestComponent(current, payload.action ?? JBS_ACTIONS.refresh, nextState, null);
        };
        if (eventName === "message") {
            stream.onmessage = onMessage;
        }
        else {
            stream.addEventListener(eventName, (event) => {
                void onMessage(event);
            });
        }
        this.streamStore.set(key, stream);
    }
    findComponent(source) {
        const explicitRef = source.getAttribute("data-jbs-component-ref");
        if (explicitRef) {
            return document.getElementById(explicitRef);
        }
        return source.closest("[data-jbs-component][data-jbs-endpoint]");
    }
    menuElements(menu) {
        return {
            trigger: menu.querySelector("[data-jbs-menu-trigger]"),
            panel: menu.querySelector("[data-jbs-menu-panel]"),
        };
    }
    focusFirstMenuItem(panel) {
        const firstItem = panel.querySelector('[role="menuitem"]:not(.disabled):not([disabled])');
        firstItem?.focus();
    }
    closeMenu(menu) {
        const { panel, trigger } = this.menuElements(menu);
        if (!panel || !trigger) {
            return;
        }
        menu.dataset.jbsMenuOpen = "false";
        panel.classList.remove("show");
        panel.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
    }
    openMenu(menu) {
        const { panel, trigger } = this.menuElements(menu);
        if (!panel || !trigger) {
            return;
        }
        this.closeAllMenus(menu);
        menu.dataset.jbsMenuOpen = "true";
        panel.hidden = false;
        panel.classList.add("show");
        trigger.setAttribute("aria-expanded", "true");
        this.focusFirstMenuItem(panel);
    }
    toggleMenu(menu) {
        if (menu.dataset.jbsMenuOpen === "true") {
            this.closeMenu(menu);
            return;
        }
        this.openMenu(menu);
    }
    closeAllMenus(except) {
        const menus = document.querySelectorAll("[data-jbs-menu]");
        for (const menu of menus) {
            if (except && menu === except) {
                continue;
            }
            this.closeMenu(menu);
        }
    }
    autocompleteElements(wrapper) {
        return {
            input: wrapper.querySelector("[data-jbs-autocomplete-input]"),
            panel: wrapper.querySelector("[data-jbs-autocomplete-panel]"),
            value: wrapper.querySelector("[data-jbs-autocomplete-value]"),
        };
    }
    autocompleteKey(wrapper) {
        const value = wrapper.querySelector("[data-jbs-autocomplete-value]");
        return value?.id || wrapper.dataset.jbsAutocompleteEndpoint || "jbs-autocomplete";
    }
    openAutocomplete(wrapper) {
        const { input, panel } = this.autocompleteElements(wrapper);
        if (!input || !panel) {
            return;
        }
        this.closeAllAutocompletes(wrapper);
        panel.hidden = false;
        panel.classList.add("show");
        input.setAttribute("aria-expanded", "true");
    }
    closeAutocomplete(wrapper) {
        const { input, panel } = this.autocompleteElements(wrapper);
        if (!input || !panel) {
            return;
        }
        panel.classList.remove("show");
        panel.hidden = true;
        input.setAttribute("aria-expanded", "false");
    }
    closeAllAutocompletes(except) {
        const wrappers = document.querySelectorAll("[data-jbs-autocomplete]");
        for (const wrapper of wrappers) {
            if (except && wrapper === except) {
                continue;
            }
            this.closeAutocomplete(wrapper);
        }
    }
    focusAutocompleteOption(panel, direction) {
        const options = panel.querySelectorAll("[data-jbs-autocomplete-option]");
        if (options.length === 0) {
            return;
        }
        const active = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        const currentIndex = active ? Array.from(options).indexOf(active) : -1;
        const nextIndex = currentIndex === -1
            ? direction > 0
                ? 0
                : options.length - 1
            : (currentIndex + direction + options.length) % options.length;
        options[nextIndex]?.focus();
    }
    selectAutocompleteOption(option) {
        const wrapper = option.closest("[data-jbs-autocomplete]");
        if (!wrapper) {
            return;
        }
        const { input, value } = this.autocompleteElements(wrapper);
        if (!input || !value) {
            return;
        }
        const nextValue = option.dataset.jbsAutocompleteValue ?? "";
        const nextLabel = option.dataset.jbsAutocompleteLabel ?? option.textContent?.trim() ?? nextValue;
        value.value = nextValue;
        value.dataset.jbsAutocompleteSelectedLabel = nextLabel;
        input.value = nextLabel;
        this.closeAutocomplete(wrapper);
        input.focus();
    }
    overlayKey(overlay) {
        return overlay.id || overlay.dataset.jbsOverlay || "jbs-overlay";
    }
    focusFirstOverlayElement(overlay) {
        const panel = overlay.querySelector("[data-jbs-overlay-panel]");
        if (!panel) {
            return;
        }
        const firstFocusable = panel.querySelector("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
        (firstFocusable ?? panel).focus();
    }
    openOverlay(overlay, trigger) {
        overlay.hidden = false;
        overlay.classList.add("show");
        overlay.setAttribute("aria-hidden", "false");
        if (trigger) {
            this.overlayReturnFocus.set(this.overlayKey(overlay), trigger);
        }
        this.closeAllAutocompletes();
        this.closeAllMenus();
        this.focusFirstOverlayElement(overlay);
    }
    closeOverlay(overlay) {
        overlay.hidden = true;
        overlay.classList.remove("show");
        overlay.setAttribute("aria-hidden", "true");
        const key = this.overlayKey(overlay);
        const returnFocus = this.overlayReturnFocus.get(key);
        returnFocus?.focus();
        this.overlayReturnFocus.delete(key);
    }
    closeTopmostOverlay() {
        const overlays = Array.from(document.querySelectorAll("[data-jbs-overlay]:not([hidden])"));
        const current = overlays[overlays.length - 1];
        if (!current) {
            return false;
        }
        this.closeOverlay(current);
        return true;
    }
    async requestAutocompleteOptions(wrapper, query) {
        const endpoint = wrapper.dataset.jbsAutocompleteEndpoint;
        const minChars = Number(wrapper.dataset.jbsAutocompleteMinChars ?? "1");
        const { panel } = this.autocompleteElements(wrapper);
        if (!endpoint || !panel) {
            return;
        }
        if (query.trim().length < minChars) {
            panel.innerHTML = "";
            this.closeAutocomplete(wrapper);
            return;
        }
        const key = this.autocompleteKey(wrapper);
        const nextRequestId = (this.autocompleteRequests.get(key) ?? 0) + 1;
        this.autocompleteRequests.set(key, nextRequestId);
        const requestUrl = new URL(endpoint, window.location.href);
        requestUrl.searchParams.set("q", query);
        const response = await this.fetchImpl(requestUrl.toString(), {
            headers: {
                Accept: JBS_HEADERS.accept,
            },
        });
        if (!response.ok) {
            throw new Error(`Autocomplete request failed with status ${response.status}.`);
        }
        if (this.autocompleteRequests.get(key) !== nextRequestId) {
            return;
        }
        panel.innerHTML = (await response.text()).trim();
        if (panel.querySelector("[data-jbs-autocomplete-option]")) {
            this.openAutocomplete(wrapper);
            return;
        }
        this.closeAutocomplete(wrapper);
    }
    buildPatchFromTrigger(component, trigger, action) {
        let patch = parseState(trigger.dataset.jbsPatch ?? null);
        const current = stripTransientState(this.getState(component));
        if (trigger.dataset.jbsRowId) {
            patch = { ...patch, row_id: trigger.dataset.jbsRowId };
        }
        if (trigger.dataset.jbsIntent) {
            patch = { ...patch, intent: trigger.dataset.jbsIntent };
        }
        if (action === JBS_ACTIONS.sort && trigger.dataset.jbsSortKey) {
            patch = {
                ...patch,
                sort_by: trigger.dataset.jbsSortKey,
                sort_dir: trigger.dataset.jbsSortDirection ?? "asc",
                page: 1,
            };
        }
        if (action === JBS_ACTIONS.page && trigger.dataset.jbsPage) {
            patch = { ...patch, page: Number(trigger.dataset.jbsPage) };
        }
        return applyStatePatch(current, patch);
    }
    async requestComponent(component, action, nextState, source) {
        const endpoint = component.dataset.jbsEndpoint;
        if (!endpoint) {
            throw new Error("Missing data-jbs-endpoint on component.");
        }
        const key = this.componentKey(component);
        const requestState = cloneState(nextState);
        const persistedState = stripTransientState(requestState);
        this.stateStore.set(key, persistedState);
        component.dataset.jbsState = JSON.stringify(persistedState);
        this.persistState(component, key, persistedState);
        const detail = {
            action,
            component,
            endpoint,
            state: cloneState(requestState),
            source,
        };
        component.dispatchEvent(new CustomEvent("jbs:before-request", { detail }));
        const requestUrl = new URL(endpoint, window.location.href);
        appendStateParams(requestUrl, requestState);
        const response = await this.fetchImpl(requestUrl.toString(), {
            headers: {
                Accept: JBS_HEADERS.accept,
                [JBS_HEADERS.marker]: "true",
                [JBS_HEADERS.component]: component.dataset.jbsComponent ?? "component",
                [JBS_HEADERS.action]: action,
            },
        });
        if (!response.ok) {
            component.dispatchEvent(new CustomEvent("jbs:request-error", { detail }));
            throw new Error(`Component request failed with status ${response.status}.`);
        }
        const html = await response.text();
        this.swapComponent(component, html, key);
    }
    swapComponent(current, html, key) {
        const template = document.createElement("template");
        template.innerHTML = html.trim();
        const next = template.content.firstElementChild;
        if (!(next instanceof HTMLElement)) {
            throw new Error("Expected component HTML to have a single root element.");
        }
        if (current.id && next.id && next.id !== current.id) {
            throw new Error("Replacement component root must keep the same id.");
        }
        if (current.dataset.jbsComponent && next.dataset.jbsComponent) {
            if (next.dataset.jbsComponent !== current.dataset.jbsComponent) {
                throw new Error("Replacement component root must keep the same component type.");
            }
        }
        next.id = next.id || current.id;
        next.dataset.jbsKey = next.dataset.jbsKey ?? key;
        next.dataset.jbsEndpoint = next.dataset.jbsEndpoint ?? current.dataset.jbsEndpoint;
        next.dataset.jbsTarget = next.dataset.jbsTarget ?? current.dataset.jbsTarget;
        next.dataset.jbsPersist = next.dataset.jbsPersist ?? current.dataset.jbsPersist;
        next.dataset.jbsStateKeys = next.dataset.jbsStateKeys ?? current.dataset.jbsStateKeys;
        next.dataset.jbsSse = next.dataset.jbsSse ?? current.dataset.jbsSse;
        next.dataset.jbsSseEvent = next.dataset.jbsSseEvent ?? current.dataset.jbsSseEvent;
        next.dataset.jbsState = next.dataset.jbsState ?? current.dataset.jbsState;
        current.replaceWith(next);
        this.closeAllAutocompletes();
        this.closeAllMenus();
        this.hydrate(next.parentNode ?? document);
        next.dispatchEvent(new CustomEvent("jbs:after-swap"));
    }
}
if (typeof window !== "undefined") {
    window.JinjaBootstrapSpa = new JBSRuntime();
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            window.JinjaBootstrapSpa.init();
        });
    }
    else {
        window.JinjaBootstrapSpa.init();
    }
}
