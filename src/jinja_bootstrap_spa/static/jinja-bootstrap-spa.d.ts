export type JBSScalar = string | number | boolean | null;
export type JBSValue = JBSScalar | JBSScalar[];
export type JBSState = Record<string, JBSValue>;
export type JBSPersistStrategy = "memory" | "querystring" | "session";
export interface JBSRuntimeOptions {
    fetchImpl?: typeof fetch;
}
export interface JBSRequestDetail {
    action: string;
    component: HTMLElement;
    endpoint: string;
    state: JBSState;
    source: HTMLElement | HTMLFormElement | null;
}
export interface JBSStreamDetail {
    component: HTMLElement;
    key: string;
    endpoint: string;
    event: string;
    data: string;
}
export declare const JBS_HEADERS: {
    readonly accept: "text/html";
    readonly marker: "X-JBS-Request";
    readonly component: "X-JBS-Component";
    readonly action: "X-JBS-Action";
};
export declare const JBS_ACTIONS: {
    readonly filter: "filter";
    readonly page: "page";
    readonly refresh: "refresh";
    readonly row: "row";
    readonly sort: "sort";
};
export declare const JBS_PERSISTENCE: {
    readonly memory: "memory";
    readonly querystring: "querystring";
    readonly session: "session";
};
export declare const JBS_STREAM_EVENTS: {
    readonly refresh: "refresh";
};
export declare class JBSRuntime {
    private readonly fetchImpl;
    private readonly stateStore;
    private readonly streamStore;
    private readonly autocompleteTimers;
    private readonly autocompleteRequests;
    private readonly overlayReturnFocus;
    private initialized;
    constructor(options?: JBSRuntimeOptions);
    init(): void;
    hydrate(root: ParentNode): void;
    getState(component: HTMLElement): JBSState;
    refresh(componentOrId: string | HTMLElement, patch?: JBSState): Promise<void>;
    private resolveComponent;
    private componentKey;
    private hydratedState;
    private persistStrategy;
    private persistState;
    private connectStream;
    private findComponent;
    private menuElements;
    private focusFirstMenuItem;
    private closeMenu;
    private openMenu;
    private toggleMenu;
    private closeAllMenus;
    private autocompleteElements;
    private autocompleteKey;
    private openAutocomplete;
    private closeAutocomplete;
    private closeAllAutocompletes;
    private focusAutocompleteOption;
    private selectAutocompleteOption;
    private overlayKey;
    private focusFirstOverlayElement;
    private openOverlay;
    private closeOverlay;
    private closeTopmostOverlay;
    private requestAutocompleteOptions;
    private handleClick;
    private handleInput;
    private handleKeydown;
    private handleSubmit;
    private buildPatchFromTrigger;
    private requestComponent;
    private swapComponent;
}
declare global {
    interface Window {
        JinjaBootstrapSpa: JBSRuntime;
    }
}
