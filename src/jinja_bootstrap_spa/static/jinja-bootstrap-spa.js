const DEFAULT_SQL_HINTS = [
    "AND",
    "OR",
    "NOT",
    "IN",
    "LIKE",
    "ILIKE",
    "has_tag('key','value')",
];
const DEFAULT_TABLE_STATE_KEYS = ["page", "page_size", "sort_by", "sort_dir", "query"];
const TRANSIENT_STATE_KEYS = new Set(["row_id", "intent"]);
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
export const JBS_STREAM_MODES = {
    replace: "replace",
    append: "append",
    prepend: "prepend",
};
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
function stableStateString(state) {
    const normalized = Object.fromEntries(Object.entries(state)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, value]) => {
        if (Array.isArray(value)) {
            return [key, [...value].map((item) => String(item))];
        }
        if (value === null) {
            return [key, null];
        }
        return [key, String(value)];
    }));
    return JSON.stringify(normalized);
}
function statesEqual(left, right) {
    return stableStateString(left) === stableStateString(right);
}
function appendStateParams(url, state) {
    for (const [key, value] of Object.entries(state)) {
        url.searchParams.delete(key);
        if (value === null || value === "") {
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
function toYmdHm(date) {
    const pad = (value) => String(value).padStart(2, "0");
    return (`${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
        ` ${pad(date.getHours())}:${pad(date.getMinutes())}`);
}
function toDatetimeLocal(date) {
    const pad = (value) => String(value).padStart(2, "0");
    return (`${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
        `T${pad(date.getHours())}:${pad(date.getMinutes())}`);
}
function parseDateInput(value) {
    const raw = String(value || "").trim();
    if (!raw) {
        return null;
    }
    const normalized = raw.includes("T") ? raw : raw.replace(" ", "T");
    const parsed = new Date(normalized);
    if (Number.isNaN(parsed.getTime())) {
        return null;
    }
    return parsed;
}
function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return rect.bottom >= 0 && rect.right >= 0 && rect.top <= window.innerHeight && rect.left <= window.innerWidth;
}
function stringListFromUnknown(value) {
    if (Array.isArray(value)) {
        return value.map((item) => String(item)).filter(Boolean);
    }
    if (typeof value === "string" && value.trim()) {
        return [value.trim()];
    }
    return [];
}
export class JBSRuntime {
    constructor(options = {}) {
        this.stateStore = new Map();
        this.streamStore = new Map();
        this.streamQueue = new Map();
        this.requestAbortControllers = new Map();
        this.requestSeq = new Map();
        this.autocompleteTimers = new Map();
        this.autocompleteRequests = new Map();
        this.autocompleteControllers = new Map();
        this.assistTimers = new Map();
        this.assistSeq = new Map();
        this.assistControllers = new Map();
        this.assistHints = new Map();
        this.overlayReturnFocus = new Map();
        this.lazyObserver = null;
        this.initialized = false;
        this.handleClick = async (event) => {
            const target = event.target instanceof HTMLElement ? event.target : null;
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
            if (target?.matches("[data-jbs-overlay]")) {
                event.preventDefault();
                this.closeOverlay(target);
                return;
            }
            const disclosureTrigger = target?.closest("[data-jbs-disclosure-trigger]");
            if (disclosureTrigger) {
                const disclosure = disclosureTrigger.closest("[data-jbs-disclosure]");
                if (disclosure) {
                    event.preventDefault();
                    this.toggleDisclosure(disclosure);
                }
                return;
            }
            const msToggle = target?.closest("[data-jbs-ms-toggle]");
            if (msToggle) {
                const wrapper = msToggle.closest("[data-jbs-multi-select]");
                if (wrapper) {
                    event.preventDefault();
                    const menu = wrapper.querySelector("[data-jbs-ms-menu]");
                    if (menu?.hidden) {
                        this.openMultiSelect(wrapper);
                    }
                    else {
                        this.closeMultiSelect(wrapper);
                    }
                }
                return;
            }
            const msOption = target?.closest("[data-jbs-ms-option]");
            if (msOption) {
                const wrapper = msOption.closest("[data-jbs-multi-select]");
                if (wrapper) {
                    event.preventDefault();
                    const single = wrapper.dataset.jbsMsSingle === "true";
                    if (single) {
                        const options = wrapper.querySelectorAll("[data-jbs-ms-option]");
                        for (const option of options) {
                            option.classList.remove("active");
                        }
                        msOption.classList.add("active");
                        this.closeMultiSelect(wrapper);
                    }
                    else {
                        msOption.classList.toggle("active");
                    }
                    this.syncMultiSelect(wrapper);
                    this.maybeSubmitMultiSelect(wrapper);
                }
                return;
            }
            const msClear = target?.closest("[data-jbs-ms-clear]");
            if (msClear) {
                const wrapper = msClear.closest("[data-jbs-multi-select]");
                if (wrapper) {
                    event.preventDefault();
                    const options = wrapper.querySelectorAll("[data-jbs-ms-option]");
                    for (const option of options) {
                        option.classList.remove("active");
                    }
                    this.syncMultiSelect(wrapper);
                    this.maybeSubmitMultiSelect(wrapper);
                }
                return;
            }
            const drpToggle = target?.closest("[data-jbs-drp-toggle]");
            if (drpToggle) {
                const wrapper = drpToggle.closest("[data-jbs-date-range]");
                if (wrapper) {
                    event.preventDefault();
                    const panel = wrapper.querySelector("[data-jbs-drp-panel]");
                    if (panel?.hidden) {
                        this.openDateRangePicker(wrapper);
                    }
                    else {
                        this.closeDateRangePicker(wrapper);
                    }
                }
                return;
            }
            const drpPreset = target?.closest("[data-jbs-drp-preset]");
            if (drpPreset) {
                const wrapper = drpPreset.closest("[data-jbs-date-range]");
                if (wrapper) {
                    event.preventDefault();
                    const minutes = Number(drpPreset.dataset.jbsMinutes ?? "0");
                    if (minutes > 0) {
                        this.applyDateRangePreset(wrapper, minutes);
                    }
                }
                return;
            }
            const drpApply = target?.closest("[data-jbs-drp-apply]");
            if (drpApply) {
                const wrapper = drpApply.closest("[data-jbs-date-range]");
                if (wrapper) {
                    event.preventDefault();
                    this.applyDateRangeCustom(wrapper);
                }
                return;
            }
            const drpClear = target?.closest("[data-jbs-drp-clear]");
            if (drpClear) {
                const wrapper = drpClear.closest("[data-jbs-date-range]");
                if (wrapper) {
                    event.preventDefault();
                    this.clearDateRange(wrapper);
                }
                return;
            }
            const assistOption = target?.closest("[data-jbs-assist-option]");
            if (assistOption) {
                const wrapper = assistOption.closest("[data-jbs-assist]");
                if (wrapper) {
                    event.preventDefault();
                    const { input } = this.assistElements(wrapper);
                    if (input) {
                        this.insertAssistOption(input, assistOption.dataset.jbsAssistOption ?? "");
                        this.closeAssistPanel(wrapper);
                    }
                }
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
            if (!target?.closest("[data-jbs-multi-select]")) {
                this.closeAllMultiSelects();
            }
            if (!target?.closest("[data-jbs-date-range]")) {
                this.closeAllDateRangePickers();
            }
            if (!target?.closest("[data-jbs-assist]")) {
                this.closeAllAssistPanels();
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
            const action = trigger.dataset.jbsAction ?? JBS_ACTIONS.refresh;
            const patch = this.buildPatchFromTrigger(component, trigger, action);
            await this.requestComponent(component, action, patch, trigger);
        };
        this.handleInput = (event) => {
            const input = event.target instanceof HTMLInputElement ? event.target : null;
            if (!input) {
                return;
            }
            if (input.hasAttribute("data-jbs-autocomplete-input")) {
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
                return;
            }
            if (input.hasAttribute("data-jbs-assist-input")) {
                const wrapper = input.closest("[data-jbs-assist]");
                if (!wrapper) {
                    return;
                }
                const key = this.assistKey(wrapper);
                const existingTimer = this.assistTimers.get(key);
                if (existingTimer !== undefined) {
                    window.clearTimeout(existingTimer);
                }
                const timer = window.setTimeout(() => {
                    void this.validateAssist(wrapper, input.value);
                    this.renderAssistOptions(wrapper, this.buildAssistOptions(wrapper, input.value));
                }, 180);
                this.assistTimers.set(key, timer);
            }
        };
        this.handleFocusIn = (event) => {
            const target = event.target instanceof HTMLElement ? event.target : null;
            const assistInput = target?.closest("[data-jbs-assist-input]");
            if (!assistInput) {
                return;
            }
            const wrapper = assistInput.closest("[data-jbs-assist]");
            if (!wrapper) {
                return;
            }
            void this.loadAssistHints(wrapper).then(() => {
                this.renderAssistOptions(wrapper, this.buildAssistOptions(wrapper, assistInput.value));
            });
        };
        this.handleKeydown = (event) => {
            const target = event.target instanceof HTMLElement ? event.target : null;
            if (!target) {
                return;
            }
            const autocompleteInput = target.closest("[data-jbs-autocomplete-input]");
            const autocompleteOption = target.closest("[data-jbs-autocomplete-option]");
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
            }
            if (event.key === "Escape") {
                if (this.closeTopmostOverlay()) {
                    return;
                }
                this.closeAllMenus();
                this.closeAllAutocompletes();
                this.closeAllMultiSelects();
                this.closeAllDateRangePickers();
                this.closeAllAssistPanels();
            }
        };
        this.handleSubmit = async (event) => {
            const form = event.target instanceof HTMLFormElement ? event.target : null;
            if (!form || !form.hasAttribute("data-jbs-form")) {
                return;
            }
            const component = form.closest("[data-jbs-component][data-jbs-endpoint]");
            if (!component) {
                return;
            }
            event.preventDefault();
            const patch = normalizeFormData(form);
            const nextState = {
                ...stripTransientState(this.getState(component)),
                ...patch,
                page: 1,
            };
            await this.requestComponent(component, JBS_ACTIONS.filter, nextState, form);
        };
        this.handlePopState = () => {
            const components = document.querySelectorAll("[data-jbs-component][data-jbs-endpoint][data-jbs-persist='querystring']");
            for (const component of components) {
                if (component.dataset.jbsHydrated !== "true") {
                    continue;
                }
                const state = stripTransientState(applyStatePatch(parseState(component.dataset.jbsState ?? null), readQueryState(component)));
                void this.requestComponent(component, JBS_ACTIONS.refresh, state, null, {
                    persist: false,
                });
            }
        };
        this.handleVisibilityChange = () => {
            if (document.visibilityState !== "visible") {
                return;
            }
            const components = document.querySelectorAll("[data-jbs-component][data-jbs-endpoint]");
            for (const component of components) {
                const key = this.componentKey(component);
                void this.flushStreamQueue(component, key);
            }
        };
        this.handleScroll = () => {
            const components = document.querySelectorAll("[data-jbs-component][data-jbs-endpoint][data-jbs-stream-pause-when-hidden='true']");
            for (const component of components) {
                const key = this.componentKey(component);
                void this.flushStreamQueue(component, key);
            }
        };
        this.fetchImpl = options.fetchImpl ?? ((input, init) => window.fetch(input, init));
    }
    init() {
        if (this.initialized) {
            return;
        }
        document.addEventListener("click", this.handleClick);
        document.addEventListener("input", this.handleInput);
        document.addEventListener("keydown", this.handleKeydown);
        document.addEventListener("submit", this.handleSubmit);
        document.addEventListener("focusin", this.handleFocusIn);
        window.addEventListener("popstate", this.handlePopState);
        document.addEventListener("visibilitychange", this.handleVisibilityChange);
        window.addEventListener("scroll", this.handleScroll, { passive: true });
        if ("IntersectionObserver" in window) {
            this.lazyObserver = new IntersectionObserver((entries) => {
                for (const entry of entries) {
                    if (!entry.isIntersecting) {
                        continue;
                    }
                    if (!(entry.target instanceof HTMLElement)) {
                        continue;
                    }
                    this.lazyObserver?.unobserve(entry.target);
                    this.activateLazyComponent(entry.target);
                }
            }, {
                root: null,
                rootMargin: "150px 0px",
                threshold: 0.01,
            });
        }
        this.hydrate(document);
        this.initialized = true;
    }
    hydrate(root) {
        this.hydrateDisclosures(root);
        this.hydrateMultiSelects(root);
        this.hydrateDateRangePickers(root);
        const components = root.querySelectorAll("[data-jbs-component][data-jbs-endpoint]");
        for (const component of components) {
            this.hydrateComponent(component, true);
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
    hydrateComponent(component, allowLazy) {
        if (allowLazy && component.dataset.jbsLazy === "true" && component.dataset.jbsHydrated !== "true") {
            this.observeLazyComponent(component);
            return;
        }
        const key = this.componentKey(component);
        const serverState = stripTransientState(parseState(component.dataset.jbsState ?? null));
        const state = this.hydratedState(component, key);
        component.dataset.jbsState = JSON.stringify(state);
        component.dataset.jbsHydrated = "true";
        this.stateStore.set(key, state);
        this.connectStream(component, key);
        void this.flushStreamQueue(component, key);
        if (!statesEqual(serverState, state)) {
            void this.requestComponent(component, JBS_ACTIONS.refresh, state, null, { persist: false });
        }
    }
    observeLazyComponent(component) {
        if (!this.lazyObserver) {
            this.activateLazyComponent(component);
            return;
        }
        this.lazyObserver.observe(component);
    }
    activateLazyComponent(component) {
        if (component.dataset.jbsHydrated === "true") {
            return;
        }
        this.hydrateComponent(component, false);
        const shouldFetch = component.dataset.jbsLazyFetch !== "false";
        if (!shouldFetch) {
            return;
        }
        void this.requestComponent(component, JBS_ACTIONS.refresh, this.getState(component), null, { persist: false });
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
        if (persist === JBS_PERSISTENCE.querystring || persist === JBS_PERSISTENCE.session) {
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
    streamMode(component, payload) {
        const explicitMode = payload.mode;
        if (explicitMode === JBS_STREAM_MODES.append ||
            explicitMode === JBS_STREAM_MODES.prepend ||
            explicitMode === JBS_STREAM_MODES.replace) {
            return explicitMode;
        }
        const attrMode = component.dataset.jbsStreamMode;
        if (attrMode === JBS_STREAM_MODES.append || attrMode === JBS_STREAM_MODES.prepend) {
            return attrMode;
        }
        return JBS_STREAM_MODES.replace;
    }
    streamBufferMax(component) {
        const parsed = Number(component.dataset.jbsStreamBufferMax ?? "100");
        if (Number.isFinite(parsed) && parsed > 0) {
            return Math.floor(parsed);
        }
        return 100;
    }
    streamMaxRows(component, payload) {
        if (typeof payload.max_rows === "number" && payload.max_rows > 0) {
            return Math.floor(payload.max_rows);
        }
        const parsed = Number(component.dataset.jbsStreamMaxRows ?? "");
        if (Number.isFinite(parsed) && parsed > 0) {
            return Math.floor(parsed);
        }
        return null;
    }
    shouldPauseStream(component) {
        if (component.dataset.jbsStreamPauseWhenHidden !== "true") {
            return false;
        }
        if (document.visibilityState === "hidden") {
            return true;
        }
        return !isElementInViewport(component);
    }
    queueStreamPayload(component, key, payload) {
        const existing = this.streamQueue.get(key) ?? [];
        existing.push(payload);
        const maxSize = this.streamBufferMax(component);
        while (existing.length > maxSize) {
            existing.shift();
        }
        this.streamQueue.set(key, existing);
        component.dispatchEvent(new CustomEvent("jbs:stream-buffered", {
            detail: { pending: existing.length, component, key },
        }));
    }
    async flushStreamQueue(component, key) {
        if (this.shouldPauseStream(component)) {
            return;
        }
        const queue = this.streamQueue.get(key);
        if (!queue || queue.length === 0) {
            return;
        }
        this.streamQueue.set(key, []);
        for (const payload of queue) {
            await this.applyStreamPayload(component, key, payload);
        }
    }
    parseStreamRows(payload) {
        if (Array.isArray(payload.rows)) {
            return payload.rows.map((row) => String(row)).filter(Boolean);
        }
        if (typeof payload.row === "string" && payload.row.trim()) {
            return [payload.row];
        }
        return [];
    }
    applyRowFragments(component, mode, payload) {
        const rows = this.parseStreamRows(payload);
        if (rows.length === 0) {
            return false;
        }
        const tableBody = component.querySelector("tbody");
        if (!(tableBody instanceof HTMLTableSectionElement)) {
            return false;
        }
        const nextRows = [];
        for (const rowHtml of rows) {
            const template = document.createElement("template");
            template.innerHTML = rowHtml.trim();
            const row = template.content.firstElementChild;
            if (!(row instanceof HTMLTableRowElement)) {
                return false;
            }
            nextRows.push(row);
        }
        if (mode === JBS_STREAM_MODES.prepend) {
            for (let index = nextRows.length - 1; index >= 0; index -= 1) {
                tableBody.prepend(nextRows[index]);
            }
        }
        else {
            for (const row of nextRows) {
                tableBody.append(row);
            }
        }
        const maxRows = this.streamMaxRows(component, payload);
        if (maxRows !== null) {
            while (tableBody.rows.length > maxRows) {
                if (mode === JBS_STREAM_MODES.prepend) {
                    tableBody.deleteRow(tableBody.rows.length - 1);
                }
                else {
                    tableBody.deleteRow(0);
                }
            }
        }
        return true;
    }
    async applyStreamPayload(component, key, payload) {
        const mode = this.streamMode(component, payload);
        const action = payload.action ?? JBS_ACTIONS.refresh;
        if (mode !== JBS_STREAM_MODES.replace && this.applyRowFragments(component, mode, payload)) {
            const nextState = stripTransientState(applyStatePatch(this.getState(component), payload.patch ?? {}));
            this.stateStore.set(key, nextState);
            component.dataset.jbsState = JSON.stringify(nextState);
            this.persistState(component, key, nextState);
            component.dispatchEvent(new CustomEvent("jbs:after-stream-patch", {
                detail: { component, key, payload, mode },
            }));
            return;
        }
        const nextState = applyStatePatch(this.getState(component), payload.patch ?? {});
        await this.requestComponent(component, action, nextState, null);
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
        const absoluteEndpoint = new URL(endpoint, window.location.href).toString();
        if (existing?.url === absoluteEndpoint) {
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
            const detail = {
                component: current,
                key,
                endpoint,
                event: eventName,
                data: event.data,
            };
            current.dispatchEvent(new CustomEvent("jbs:stream-event", { detail }));
            if (this.shouldPauseStream(current)) {
                this.queueStreamPayload(current, key, payload);
                return;
            }
            await this.applyStreamPayload(current, key, payload);
        };
        if (eventName === "message") {
            stream.onmessage = (event) => {
                void onMessage(event);
            };
        }
        else {
            stream.addEventListener(eventName, (event) => {
                if (!(event instanceof MessageEvent)) {
                    return;
                }
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
        const firstItem = panel.querySelector("[role='menuitem']:not(.disabled):not([disabled])");
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
        const element = option;
        const nextValue = element.dataset.jbsAutocompleteValue ?? "";
        const nextLabel = element.dataset.jbsAutocompleteLabel ??
            element.textContent?.trim() ??
            nextValue;
        value.value = nextValue;
        value.dataset.jbsAutocompleteSelectedLabel = nextLabel;
        input.value = nextLabel;
        this.closeAutocomplete(wrapper);
        input.focus();
    }
    overlayKey(overlay) {
        const element = overlay;
        return element.id || element.dataset.jbsOverlay || "jbs-overlay";
    }
    focusFirstOverlayElement(overlay) {
        const panel = overlay.querySelector("[data-jbs-overlay-panel]");
        if (!(panel instanceof HTMLElement)) {
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
        this.closeAllMultiSelects();
        this.closeAllDateRangePickers();
        this.closeAllAssistPanels();
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
    multiSelectElements(wrapper) {
        return {
            toggle: wrapper.querySelector("[data-jbs-ms-toggle]"),
            label: wrapper.querySelector("[data-jbs-ms-label]"),
            menu: wrapper.querySelector("[data-jbs-ms-menu]"),
            hidden: wrapper.querySelector("[data-jbs-ms-hidden]"),
            clear: wrapper.querySelector("[data-jbs-ms-clear]"),
        };
    }
    hydrateMultiSelects(root) {
        const wrappers = root.querySelectorAll("[data-jbs-multi-select]");
        for (const wrapper of wrappers) {
            this.syncMultiSelect(wrapper);
        }
    }
    selectedMultiSelectOptions(wrapper) {
        const options = wrapper.querySelectorAll("[data-jbs-ms-option]");
        return Array.from(options).filter((option) => option.classList.contains("active"));
    }
    syncMultiSelect(wrapper) {
        const { label, hidden, clear, toggle } = this.multiSelectElements(wrapper);
        if (!hidden || !toggle || !label) {
            return;
        }
        const single = wrapper.dataset.jbsMsSingle === "true";
        const inputName = wrapper.dataset.jbsMsInputName || "value";
        const placeholder = wrapper.dataset.jbsMsPlaceholder || "All";
        const selectedOptions = this.selectedMultiSelectOptions(wrapper);
        for (const option of wrapper.querySelectorAll("[data-jbs-ms-option]")) {
            const selected = option.classList.contains("active");
            option.setAttribute("aria-pressed", selected ? "true" : "false");
            const check = option.querySelector("[data-jbs-ms-check]");
            if (check) {
                check.classList.toggle("invisible", !selected);
            }
        }
        hidden.innerHTML = "";
        for (const option of selectedOptions) {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = inputName;
            input.value = option.dataset.jbsMsValue ?? "";
            hidden.append(input);
        }
        if (selectedOptions.length === 0) {
            label.textContent = placeholder;
        }
        else if (single || selectedOptions.length === 1) {
            const text = selectedOptions[0]?.textContent?.trim() ?? selectedOptions[0]?.dataset.jbsMsValue ?? placeholder;
            label.textContent = text;
        }
        else {
            label.textContent = `${selectedOptions.length} selected`;
        }
        if (clear) {
            clear.hidden = selectedOptions.length === 0;
        }
    }
    openMultiSelect(wrapper) {
        const { menu, toggle } = this.multiSelectElements(wrapper);
        if (!menu || !toggle) {
            return;
        }
        this.closeAllMultiSelects(wrapper);
        menu.hidden = false;
        menu.classList.add("show");
        toggle.setAttribute("aria-expanded", "true");
    }
    closeMultiSelect(wrapper) {
        const { menu, toggle } = this.multiSelectElements(wrapper);
        if (!menu || !toggle) {
            return;
        }
        menu.classList.remove("show");
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
    }
    closeAllMultiSelects(except) {
        const wrappers = document.querySelectorAll("[data-jbs-multi-select]");
        for (const wrapper of wrappers) {
            if (except && wrapper === except) {
                continue;
            }
            this.closeMultiSelect(wrapper);
        }
    }
    maybeSubmitMultiSelect(wrapper) {
        if (wrapper.dataset.jbsMsAutoSubmit !== "true") {
            return;
        }
        const form = wrapper.closest("form");
        if (form instanceof HTMLFormElement) {
            form.requestSubmit();
        }
    }
    disclosureElements(wrapper) {
        return {
            trigger: wrapper.querySelector("[data-jbs-disclosure-trigger]"),
            panel: wrapper.querySelector("[data-jbs-disclosure-panel]"),
        };
    }
    hydrateDisclosures(root) {
        const wrappers = root.querySelectorAll("[data-jbs-disclosure]");
        for (const wrapper of wrappers) {
            const { trigger, panel } = this.disclosureElements(wrapper);
            if (!trigger || !panel) {
                continue;
            }
            const expanded = trigger.getAttribute("aria-expanded") === "true";
            panel.hidden = !expanded;
        }
    }
    toggleDisclosure(wrapper) {
        const { trigger, panel } = this.disclosureElements(wrapper);
        if (!trigger || !panel) {
            return;
        }
        const expanded = trigger.getAttribute("aria-expanded") === "true";
        trigger.setAttribute("aria-expanded", expanded ? "false" : "true");
        panel.hidden = expanded;
    }
    dateRangeElements(wrapper) {
        return {
            fromInput: wrapper.querySelector("[data-jbs-drp-from]"),
            toInput: wrapper.querySelector("[data-jbs-drp-to]"),
            toggle: wrapper.querySelector("[data-jbs-drp-toggle]"),
            panel: wrapper.querySelector("[data-jbs-drp-panel]"),
            customFrom: wrapper.querySelector("[data-jbs-drp-custom-from]"),
            customTo: wrapper.querySelector("[data-jbs-drp-custom-to]"),
        };
    }
    hydrateDateRangePickers(root) {
        const wrappers = root.querySelectorAll("[data-jbs-date-range]");
        for (const wrapper of wrappers) {
            const { panel, toggle } = this.dateRangeElements(wrapper);
            if (!panel || !toggle) {
                continue;
            }
            panel.hidden = true;
            toggle.setAttribute("aria-expanded", "false");
        }
    }
    openDateRangePicker(wrapper) {
        const { panel, toggle, fromInput, toInput, customFrom, customTo } = this.dateRangeElements(wrapper);
        if (!panel || !toggle) {
            return;
        }
        this.closeAllDateRangePickers(wrapper);
        const fromDate = fromInput ? parseDateInput(fromInput.value) : null;
        const toDate = toInput ? parseDateInput(toInput.value) : null;
        if (customFrom) {
            customFrom.value = fromDate ? toDatetimeLocal(fromDate) : "";
        }
        if (customTo) {
            customTo.value = toDate ? toDatetimeLocal(toDate) : "";
        }
        panel.hidden = false;
        panel.classList.add("show");
        toggle.setAttribute("aria-expanded", "true");
    }
    closeDateRangePicker(wrapper) {
        const { panel, toggle } = this.dateRangeElements(wrapper);
        if (!panel || !toggle) {
            return;
        }
        panel.classList.remove("show");
        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
    }
    closeAllDateRangePickers(except) {
        const wrappers = document.querySelectorAll("[data-jbs-date-range]");
        for (const wrapper of wrappers) {
            if (except && wrapper === except) {
                continue;
            }
            this.closeDateRangePicker(wrapper);
        }
    }
    maybeSubmitDateRange(wrapper) {
        if (wrapper.dataset.jbsDrpAutoSubmit !== "true") {
            return;
        }
        const form = wrapper.closest("form");
        if (form instanceof HTMLFormElement) {
            form.requestSubmit();
        }
    }
    applyDateRangePreset(wrapper, minutes) {
        const { fromInput, toInput } = this.dateRangeElements(wrapper);
        if (!fromInput || !toInput) {
            return;
        }
        const now = new Date();
        const from = new Date(now.getTime() - minutes * 60000);
        fromInput.value = toYmdHm(from);
        toInput.value = "";
        this.closeDateRangePicker(wrapper);
        this.maybeSubmitDateRange(wrapper);
    }
    applyDateRangeCustom(wrapper) {
        const { fromInput, toInput, customFrom, customTo } = this.dateRangeElements(wrapper);
        if (!fromInput || !toInput) {
            return;
        }
        const from = customFrom ? parseDateInput(customFrom.value) : null;
        const to = customTo ? parseDateInput(customTo.value) : null;
        fromInput.value = from ? toYmdHm(from) : "";
        toInput.value = to ? toYmdHm(to) : "";
        this.closeDateRangePicker(wrapper);
        this.maybeSubmitDateRange(wrapper);
    }
    clearDateRange(wrapper) {
        const { fromInput, toInput, customFrom, customTo } = this.dateRangeElements(wrapper);
        if (fromInput) {
            fromInput.value = "";
        }
        if (toInput) {
            toInput.value = "";
        }
        if (customFrom) {
            customFrom.value = "";
        }
        if (customTo) {
            customTo.value = "";
        }
        this.closeDateRangePicker(wrapper);
        this.maybeSubmitDateRange(wrapper);
    }
    assistElements(wrapper) {
        return {
            input: wrapper.querySelector("[data-jbs-assist-input]"),
            panel: wrapper.querySelector("[data-jbs-assist-panel]"),
            status: wrapper.querySelector("[data-jbs-assist-status]"),
        };
    }
    assistKey(wrapper) {
        const { input } = this.assistElements(wrapper);
        return input?.id || wrapper.dataset.jbsAssist || "jbs-assist";
    }
    openAssistPanel(wrapper) {
        const { panel, input } = this.assistElements(wrapper);
        if (!panel || !input) {
            return;
        }
        this.closeAllAssistPanels(wrapper);
        panel.hidden = false;
        panel.classList.add("show");
        input.setAttribute("aria-expanded", "true");
    }
    closeAssistPanel(wrapper) {
        const { panel, input } = this.assistElements(wrapper);
        if (!panel || !input) {
            return;
        }
        panel.classList.remove("show");
        panel.hidden = true;
        input.setAttribute("aria-expanded", "false");
    }
    closeAllAssistPanels(except) {
        const wrappers = document.querySelectorAll("[data-jbs-assist]");
        for (const wrapper of wrappers) {
            if (except && wrapper === except) {
                continue;
            }
            this.closeAssistPanel(wrapper);
        }
    }
    setAssistStatus(wrapper, level, message) {
        const { status } = this.assistElements(wrapper);
        if (!status) {
            return;
        }
        status.textContent = message;
        status.classList.remove("text-danger", "text-success", "text-warning");
        if (level === "error") {
            status.classList.add("text-danger");
        }
        else if (level === "success") {
            status.classList.add("text-success");
        }
        else if (level === "warning") {
            status.classList.add("text-warning");
        }
    }
    renderAssistOptions(wrapper, options) {
        const { panel } = this.assistElements(wrapper);
        if (!panel) {
            return;
        }
        panel.innerHTML = "";
        if (options.length === 0) {
            this.closeAssistPanel(wrapper);
            return;
        }
        for (const option of options) {
            const li = document.createElement("li");
            const button = document.createElement("button");
            button.type = "button";
            button.className = "dropdown-item font-monospace small";
            button.dataset.jbsAssistOption = option;
            button.textContent = option;
            li.append(button);
            panel.append(li);
        }
        this.openAssistPanel(wrapper);
    }
    insertAssistOption(input, option) {
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? start;
        const before = input.value.slice(0, start);
        const after = input.value.slice(end);
        const needsSpaceBefore = before.length > 0 && !/\s$/.test(before);
        const nextValue = `${before}${needsSpaceBefore ? " " : ""}${option}${after}`;
        const cursor = (before + (needsSpaceBefore ? " " : "") + option).length;
        input.value = nextValue;
        input.setSelectionRange(cursor, cursor);
        input.dispatchEvent(new Event("input", { bubbles: true }));
    }
    buildAssistOptions(wrapper, inputValue) {
        const key = this.assistKey(wrapper);
        const hints = this.assistHints.get(key) ?? [];
        const type = wrapper.dataset.jbsAssist ?? "sql";
        const candidates = type === "sql" ? [...DEFAULT_SQL_HINTS, ...hints] : hints;
        if (candidates.length === 0) {
            return [];
        }
        const query = inputValue.trim().toLowerCase();
        const matches = candidates.filter((candidate) => {
            if (!query) {
                return true;
            }
            return candidate.toLowerCase().includes(query);
        });
        return Array.from(new Set(matches)).slice(0, 12);
    }
    async loadAssistHints(wrapper) {
        const endpoint = wrapper.dataset.jbsAssistHintsEndpoint;
        if (!endpoint) {
            return;
        }
        const key = this.assistKey(wrapper);
        if (this.assistHints.has(key)) {
            return;
        }
        try {
            const response = await this.fetchImpl(endpoint, {
                headers: { Accept: "application/json" },
            });
            if (!response.ok) {
                return;
            }
            const payload = (await response.json());
            const hints = [
                ...stringListFromUnknown(payload.hints),
                ...stringListFromUnknown(payload.fields),
                ...stringListFromUnknown(payload.operators),
            ];
            this.assistHints.set(key, Array.from(new Set(hints)));
        }
        catch {
            this.assistHints.set(key, []);
        }
    }
    async validateAssist(wrapper, inputValue) {
        const endpoint = wrapper.dataset.jbsAssistValidateEndpoint;
        if (!endpoint) {
            return;
        }
        const key = this.assistKey(wrapper);
        const seq = (this.assistSeq.get(key) ?? 0) + 1;
        this.assistSeq.set(key, seq);
        this.assistControllers.get(key)?.abort();
        const controller = new AbortController();
        this.assistControllers.set(key, controller);
        const valueKey = wrapper.dataset.jbsAssistValueKey || "query";
        const body = JSON.stringify({ [valueKey]: inputValue });
        try {
            const response = await this.fetchImpl(endpoint, {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                },
                body,
                signal: controller.signal,
            });
            if (this.assistSeq.get(key) !== seq) {
                return;
            }
            if (!response.ok) {
                this.setAssistStatus(wrapper, "error", `Validation failed (${response.status}).`);
                return;
            }
            const payload = (await response.json());
            const ok = Boolean(payload.ok);
            const issues = Array.isArray(payload.issues) ? payload.issues : [];
            const firstIssue = issues[0];
            if (ok) {
                const message = String(payload.message || "Expression looks valid.");
                this.setAssistStatus(wrapper, "success", message);
            }
            else if (firstIssue) {
                const level = String(firstIssue.level || "error").toLowerCase();
                const message = String(firstIssue.message || "Invalid expression.");
                this.setAssistStatus(wrapper, level === "warning" ? "warning" : "error", message);
            }
            else {
                const message = String(payload.message || "Invalid expression.");
                this.setAssistStatus(wrapper, "error", message);
            }
        }
        catch (error) {
            if (error instanceof DOMException && error.name === "AbortError") {
                return;
            }
            this.setAssistStatus(wrapper, "warning", "Validation unavailable.");
        }
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
        this.autocompleteControllers.get(key)?.abort();
        const controller = new AbortController();
        this.autocompleteControllers.set(key, controller);
        const requestUrl = new URL(endpoint, window.location.href);
        requestUrl.searchParams.set("q", query);
        const response = await this.fetchImpl(requestUrl.toString(), {
            headers: { Accept: JBS_HEADERS.accept },
            signal: controller.signal,
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
    async requestComponent(component, action, nextState, source, options = {}) {
        const endpoint = component.dataset.jbsEndpoint;
        if (!endpoint) {
            throw new Error("Missing data-jbs-endpoint on component.");
        }
        const key = this.componentKey(component);
        const requestState = cloneState(nextState);
        const persistedState = stripTransientState(requestState);
        this.stateStore.set(key, persistedState);
        component.dataset.jbsState = JSON.stringify(persistedState);
        if (options.persist !== false) {
            this.persistState(component, key, persistedState);
        }
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
        this.requestAbortControllers.get(key)?.abort();
        const controller = new AbortController();
        this.requestAbortControllers.set(key, controller);
        const seq = (this.requestSeq.get(key) ?? 0) + 1;
        this.requestSeq.set(key, seq);
        try {
            const response = await this.fetchImpl(requestUrl.toString(), {
                headers: {
                    Accept: JBS_HEADERS.accept,
                    [JBS_HEADERS.marker]: "true",
                    [JBS_HEADERS.component]: component.dataset.jbsComponent ?? "component",
                    [JBS_HEADERS.action]: action,
                },
                signal: controller.signal,
            });
            if (this.requestSeq.get(key) !== seq) {
                return;
            }
            if (!response.ok) {
                component.dispatchEvent(new CustomEvent("jbs:request-error", { detail }));
                throw new Error(`Component request failed with status ${response.status}.`);
            }
            const html = await response.text();
            this.swapComponent(component, html, key);
        }
        catch (error) {
            if (error instanceof DOMException && error.name === "AbortError") {
                return;
            }
            throw error;
        }
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
        next.dataset.jbsStreamMode = next.dataset.jbsStreamMode ?? current.dataset.jbsStreamMode;
        next.dataset.jbsStreamMaxRows = next.dataset.jbsStreamMaxRows ?? current.dataset.jbsStreamMaxRows;
        next.dataset.jbsStreamPauseWhenHidden =
            next.dataset.jbsStreamPauseWhenHidden ?? current.dataset.jbsStreamPauseWhenHidden;
        next.dataset.jbsStreamBufferMax =
            next.dataset.jbsStreamBufferMax ?? current.dataset.jbsStreamBufferMax;
        next.dataset.jbsLazy = next.dataset.jbsLazy ?? current.dataset.jbsLazy;
        current.replaceWith(next);
        this.closeAllAutocompletes();
        this.closeAllMenus();
        this.closeAllMultiSelects();
        this.closeAllDateRangePickers();
        this.closeAllAssistPanels();
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
