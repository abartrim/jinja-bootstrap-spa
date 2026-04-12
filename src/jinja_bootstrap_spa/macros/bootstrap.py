"""Packaged Jinja macros for Bootstrap 5 UI primitives.

Jinja macros normally live in `.html` files, but keeping the canonical source in
Python makes it easier for AI agents and library authors to inspect, register,
and test them programmatically. The helpers in this module publish a virtual
template called ``jinja_bootstrap_spa/bootstrap_macros.html`` through a
``DictLoader`` so applications can import the macros like any other template.
"""

from __future__ import annotations

from jinja2 import BaseLoader, ChoiceLoader, DictLoader, Environment

MACRO_TEMPLATE_NAME = "jinja_bootstrap_spa/bootstrap_macros.html"

BOOTSTRAP_MACROS = """
{%- macro button(label, href=None, variant="primary", size=None, button_type="button",
                 outline=False, disabled=False, class_name="", id=None,
                 jbs_action=None, jbs_component_ref=None, jbs_patch=None,
                 jbs_page=None, jbs_sort_key=None, jbs_sort_direction=None,
                 jbs_row_id=None, jbs_intent=None,
                 attrs="") -%}
  {%- set tag = "a" if href else "button" -%}
  {%- set btn_variant = (
        "outline-" ~ variant
        if outline and not variant.startswith("outline-")
        else variant
      ) -%}
  {%- set classes = "btn btn-" ~ btn_variant -%}
  {%- if size -%}
    {%- set classes = classes ~ " btn-" ~ size -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set classes = classes ~ " " ~ class_name -%}
  {%- endif -%}
  <{{ tag }}
    class="{{ classes }}"
    {%- if id %} id="{{ id }}"{% endif -%}
    {%- if href %} href="{{ href }}"{% else %} type="{{ button_type }}"{% endif -%}
    {%- if disabled %}
      {{ "aria-disabled=\\"true\\" tabindex=\\"-1\\"" if href else "disabled" }}
    {% endif -%}
    {%- if jbs_action %} data-jbs-action="{{ jbs_action }}"{% endif -%}
    {%- if jbs_component_ref %}
      data-jbs-component-ref="{{ jbs_component_ref }}"
    {% endif -%}
    {%- if jbs_patch %} data-jbs-patch='{{ jbs_patch|tojson }}'{% endif -%}
    {%- if jbs_page is not none %} data-jbs-page="{{ jbs_page }}"{% endif -%}
    {%- if jbs_sort_key %} data-jbs-sort-key="{{ jbs_sort_key }}"{% endif -%}
    {%- if jbs_sort_direction %}
      data-jbs-sort-direction="{{ jbs_sort_direction }}"
    {% endif -%}
    {%- if jbs_row_id %} data-jbs-row-id="{{ jbs_row_id }}"{% endif -%}
    {%- if jbs_intent %} data-jbs-intent="{{ jbs_intent }}"{% endif -%}
    {%- if attrs %} {{ attrs|safe }}{% endif -%}
  >{{ label }}</{{ tag }}>
{%- endmacro -%}

{%- macro action_menu(menu_id, label="Actions", items=None, variant="outline-secondary",
                      size="sm", align="end", button_class="", menu_class="",
                      class_name="", attrs="") -%}
  {%- set items = items or [] -%}
  {%- set trigger_id = menu_id ~ "-trigger" -%}
  {%- set panel_id = menu_id ~ "-panel" -%}
  {%- set wrapper_classes = "dropdown jbs-action-menu d-inline-block" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set trigger_classes = "btn btn-" ~ variant ~ " dropdown-toggle" -%}
  {%- if size -%}
    {%- set trigger_classes = trigger_classes ~ " btn-" ~ size -%}
  {%- endif -%}
  {%- if button_class -%}
    {%- set trigger_classes = trigger_classes ~ " " ~ button_class -%}
  {%- endif -%}
  {%- set panel_classes = "dropdown-menu shadow-sm" -%}
  {%- if align == "start" -%}
    {%- set panel_classes = panel_classes ~ " dropdown-menu-start" -%}
  {%- else -%}
    {%- set panel_classes = panel_classes ~ " dropdown-menu-end" -%}
  {%- endif -%}
  {%- if menu_class -%}
    {%- set panel_classes = panel_classes ~ " " ~ menu_class -%}
  {%- endif -%}
  <div id="{{ menu_id }}"
       class="{{ wrapper_classes }}"
       data-jbs-menu
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <button type="button"
            id="{{ trigger_id }}"
            class="{{ trigger_classes }}"
            data-jbs-menu-trigger
            aria-expanded="false"
            aria-haspopup="menu"
            aria-controls="{{ panel_id }}">
      {{ label }}
    </button>
    <div id="{{ panel_id }}"
         class="{{ panel_classes }}"
         data-jbs-menu-panel
         role="menu"
         aria-labelledby="{{ trigger_id }}"
         hidden>
      {%- for item in items %}
        {%- if item.divider %}
          <hr class="dropdown-divider">
        {%- else %}
          {%- set tag = "a" if item.href else "button" -%}
          {%- set item_classes = "dropdown-item" -%}
          {%- if item.variant == "danger" %}
            {%- set item_classes = item_classes ~ " text-danger" -%}
          {%- endif -%}
          {%- if item.disabled %}
            {%- set item_classes = item_classes ~ " disabled" -%}
          {%- endif -%}
          {%- if item.class_name %}
            {%- set item_classes = item_classes ~ " " ~ item.class_name -%}
          {%- endif -%}
          <{{ tag }}
            class="{{ item_classes }}"
            {%- if item.href %}
              href="{{ item.href }}"
            {% else %}
              type="button"
            {% endif -%}
            role="menuitem"
            {%- if item.disabled %}
              {{
                "aria-disabled=\\"true\\" tabindex=\\"-1\\""
                if item.href
                else "disabled"
              }}
            {% endif -%}
            {%- if item.jbs_action %}
              data-jbs-action="{{ item.jbs_action }}"
            {% endif -%}
            {%- if item.jbs_component_ref %}
              data-jbs-component-ref="{{ item.jbs_component_ref }}"
            {% endif -%}
            {%- if item.jbs_patch %}
              data-jbs-patch='{{ item.jbs_patch|tojson }}'
            {% endif -%}
            {%- if item.jbs_page is not none %}
              data-jbs-page="{{ item.jbs_page }}"
            {% endif -%}
            {%- if item.jbs_sort_key %}
              data-jbs-sort-key="{{ item.jbs_sort_key }}"
            {% endif -%}
            {%- if item.jbs_sort_direction %}
              data-jbs-sort-direction="{{ item.jbs_sort_direction }}"
            {% endif -%}
            {%- if item.jbs_row_id %}
              data-jbs-row-id="{{ item.jbs_row_id }}"
            {% endif -%}
            {%- if item.jbs_intent %}
              data-jbs-intent="{{ item.jbs_intent }}"
            {% endif -%}
            {%- if item.attrs %} {{ item.attrs|safe }}{% endif -%}
          >
            {%- if item.html %}
              {{ item.label|safe }}
            {% else %}
              {{ item.label }}
            {% endif -%}
          </{{ tag }}>
        {%- endif %}
      {%- endfor %}
    </div>
  </div>
{%- endmacro -%}

{%- macro tabs(group_id, items, active=None, variant="pills", class_name="",
               attrs="") -%}
  {%- set items = items or [] -%}
  {%- set nav_classes = "nav gap-2" -%}
  {%- if variant == "tabs" -%}
    {%- set nav_classes = nav_classes ~ " nav-tabs" -%}
  {%- else -%}
    {%- set nav_classes = nav_classes ~ " nav-pills" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set nav_classes = nav_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div id="{{ group_id }}"
       class="{{ nav_classes }}"
       role="tablist"
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- for item in items %}
      {%- set item_value = (
            item.value if item.value is defined else item.label
          ) -%}
      {%- set is_active = (
            item.active if item.active is defined else active == item_value
          ) -%}
      {%- set tag = "a" if item.href else "button" -%}
      <{{ tag }}
        class="nav-link{% if is_active %} active{% endif %}"
        {%- if item.href %}
          href="{{ item.href }}"
        {% else %}
          type="button"
        {% endif -%}
        role="tab"
        aria-selected="{{ 'true' if is_active else 'false' }}"
        {%- if item.jbs_action %} data-jbs-action="{{ item.jbs_action }}"{% endif -%}
        {%- if item.jbs_component_ref %}
          data-jbs-component-ref="{{ item.jbs_component_ref }}"
        {% endif -%}
        {%- if item.jbs_patch %}
          data-jbs-patch='{{ item.jbs_patch|tojson }}'
        {% endif -%}
        {%- if item.attrs %} {{ item.attrs|safe }}{% endif -%}
      >
        {{ item.label }}
      </{{ tag }}>
    {%- endfor %}
  </div>
{%- endmacro -%}

{%- macro card(title=None, body="", footer=None, class_name="", id=None, attrs="") -%}
  <div class="card{% if class_name %} {{ class_name }}{% endif %}"
       {%- if id %} id="{{ id }}"{% endif -%}
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title %}
      <div class="card-header">{{ title }}</div>
    {%- endif %}
    <div class="card-body">{{ body }}</div>
    {%- if footer %}
      <div class="card-footer">{{ footer }}</div>
    {%- endif %}
  </div>
{%- endmacro -%}

{%- macro modal(overlay_id, title=None, body="", footer=None, size="lg",
                close_label="Close", class_name="", attrs="") -%}
  {%- set dialog_classes = "card shadow-lg border-0 w-100" -%}
  {%- if size == "sm" -%}
    {%- set dialog_classes = dialog_classes ~ " col-12 col-md-6 col-lg-4" -%}
  {%- elif size == "xl" -%}
    {%- set dialog_classes = dialog_classes ~ " col-12 col-xl-10" -%}
  {%- else -%}
    {%- set dialog_classes = dialog_classes ~ " col-12 col-lg-8 col-xl-6" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set dialog_classes = dialog_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div id="{{ overlay_id }}"
       class="jbs-overlay position-fixed top-0 start-0 w-100 h-100 z-3"
       data-jbs-overlay="modal"
       role="dialog"
       aria-modal="true"
       aria-hidden="true"
       hidden
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="position-absolute top-0 start-0 w-100 h-100 bg-dark
                bg-opacity-50"></div>
    <div class="position-relative w-100 h-100 d-flex align-items-center
                justify-content-center p-3">
      <div class="position-relative {{ dialog_classes }}"
           data-jbs-overlay-panel
           tabindex="-1">
        <div class="card-header bg-body d-flex align-items-center
                    justify-content-between gap-3">
          <div>
            {%- if title %}
              <h2 class="h5 mb-0">{{ title }}</h2>
            {%- endif %}
          </div>
          <button type="button"
                  class="btn btn-sm btn-outline-secondary"
                  data-jbs-overlay-close>
            {{ close_label }}
          </button>
        </div>
        <div class="card-body">
          {{ body|safe }}
        </div>
        {%- if footer %}
          <div class="card-footer bg-body">
            {{ footer|safe }}
          </div>
        {%- endif %}
      </div>
    </div>
  </div>
{%- endmacro -%}

{%- macro drawer(overlay_id, title=None, body="", footer=None, placement="end",
                 width="420px", close_label="Close", class_name="", attrs="") -%}
  {%- set justify_class = (
        "justify-content-end"
        if placement != "start"
        else "justify-content-start"
      ) -%}
  {%- set panel_classes = "bg-body shadow-lg h-100 w-100 d-flex flex-column" -%}
  {%- if class_name -%}
    {%- set panel_classes = panel_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div id="{{ overlay_id }}"
       class="jbs-overlay position-fixed top-0 start-0 w-100 h-100 z-3"
       data-jbs-overlay="drawer"
       role="dialog"
       aria-modal="true"
       aria-hidden="true"
       hidden
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="position-absolute top-0 start-0 w-100 h-100 bg-dark
                bg-opacity-50"></div>
    <div class="position-relative w-100 h-100 d-flex {{ justify_class }}">
      <aside class="position-relative {{ panel_classes }}"
             data-jbs-overlay-panel
             tabindex="-1"
             style="max-width: {{ width }};">
        <div class="border-bottom px-4 py-3 d-flex align-items-center
                    justify-content-between gap-3">
          <div>
            {%- if title %}
              <h2 class="h5 mb-0">{{ title }}</h2>
            {%- endif %}
          </div>
          <button type="button"
                  class="btn btn-sm btn-outline-secondary"
                  data-jbs-overlay-close>
            {{ close_label }}
          </button>
        </div>
        <div class="flex-grow-1 overflow-auto px-4 py-3">
          {{ body|safe }}
        </div>
        {%- if footer %}
          <div class="border-top px-4 py-3 bg-body">
            {{ footer|safe }}
          </div>
        {%- endif %}
      </aside>
    </div>
  </div>
{%- endmacro -%}

{%- macro status_region(region_id=None, title=None, message="", variant="info",
                        dismissible=True, class_name="", attrs="") -%}
  {%- set region_classes = "alert alert-" ~ variant -%}
  {%- if dismissible -%}
    {%- set region_classes = region_classes ~ " alert-dismissible" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set region_classes = region_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="{{ region_classes }}"
       role="status"
       aria-live="polite"
       data-jbs-status-region
       {%- if region_id %} id="{{ region_id }}"{% endif -%}
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if dismissible %}
      <button type="button"
              class="btn-close"
              aria-label="Dismiss"
              data-jbs-status-dismiss></button>
    {%- endif %}
    {%- if title %}
      <h3 class="h6 mb-1">{{ title }}</h3>
    {%- endif %}
    <div>{{ message }}</div>
  </div>
{%- endmacro -%}

{%- macro filter_accordion(
      accordion_id, title="Filters", body="", icon_class="bi bi-funnel",
      open=True, active_badge=False, header_suffix="", class_name="", attrs=""
    ) -%}
  {%- set panel_id = accordion_id ~ "-panel" -%}
  {%- set trigger_id = accordion_id ~ "-trigger" -%}
  {%- set wrapper_classes = "card border-secondary jbs-filter-accordion mb-3" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section id="{{ accordion_id }}"
           class="{{ wrapper_classes }}"
           data-jbs-disclosure
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <header class="card-header py-2">
      <button type="button"
              id="{{ trigger_id }}"
              class="btn btn-link p-0 text-decoration-none d-flex align-items-center
                     gap-2 text-body fw-semibold w-100"
              data-jbs-disclosure-trigger
              aria-expanded="{{ 'true' if open else 'false' }}"
              aria-controls="{{ panel_id }}">
        <i class="{{ icon_class }}" aria-hidden="true"></i>
        <span>{{ title }}</span>
        {%- if active_badge %}
          <span class="badge text-bg-primary ms-1">Active</span>
        {%- endif %}
        {%- if header_suffix %}
          <span class="ms-auto">{{ header_suffix|safe }}</span>
        {%- endif %}
      </button>
    </header>
    <div id="{{ panel_id }}"
         class="card-body"
         data-jbs-disclosure-panel
         role="region"
         aria-labelledby="{{ trigger_id }}"
         {%- if not open %} hidden{% endif -%}>
      {{ body|safe }}
    </div>
  </section>
{%- endmacro -%}

{%- macro filter_multi_select(name, label, options, selected_values=None,
                              placeholder=None, single_select=False,
                              auto_submit=True, input_name=None,
                              class_name="", attrs="") -%}
  {%- set input_name = input_name or name -%}
  {%- set selected_values = selected_values or [] -%}
  {%- set selected_values = selected_values | map('string') | list -%}
  {%- set count = selected_values|length -%}
  {%- set placeholder = placeholder or ("All " ~ label|lower) -%}
  {%- set button_text = (
        selected_values[0]
        if single_select and count == 1
        else (count ~ " selected" if count > 0 else placeholder)
      ) -%}
  {%- set wrapper_classes = "jbs-multi-select position-relative" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="{{ wrapper_classes }}"
       data-jbs-multi-select
       data-jbs-ms-single="{{ 'true' if single_select else 'false' }}"
       data-jbs-ms-auto-submit="{{ 'true' if auto_submit else 'false' }}"
       data-jbs-ms-input-name="{{ input_name }}"
       data-jbs-ms-placeholder="{{ placeholder }}"
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <label class="form-label small text-body-secondary">{{ label }}</label>
    <div class="d-flex align-items-center gap-2">
      <button type="button"
              class="form-select form-select-sm text-start"
              data-jbs-ms-toggle
              aria-expanded="false">
        <span data-jbs-ms-label>{{ button_text }}</span>
      </button>
      <button type="button"
              class="btn btn-sm btn-outline-secondary"
              data-jbs-ms-clear
              title="Clear {{ label|lower }}"
              {%- if count == 0 %} hidden{% endif -%}>
        <i class="bi bi-x" aria-hidden="true"></i>
      </button>
    </div>
    <div class="dropdown-menu w-100 shadow-sm mt-1"
         data-jbs-ms-menu
         role="listbox"
         hidden>
      {%- for option in options %}
        {%- set option_value = (
              option.value if option.value is defined
              else (option["value"] if option is mapping else option)
            ) -%}
        {%- set option_label = (
              option.label if option.label is defined
              else (
                option["label"]
                if option is mapping and "label" in option
                else option_value
              )
            ) -%}
        {%- set option_value_str = option_value|string -%}
        {%- set is_selected = option_value_str in selected_values -%}
        <button type="button"
                class="dropdown-item d-flex align-items-center gap-2
                       {% if is_selected %} active{% endif %}"
                data-jbs-ms-option
                data-jbs-ms-value="{{ option_value_str }}"
                aria-pressed="{{ 'true' if is_selected else 'false' }}">
          <i class="bi bi-check2{% if not is_selected %} invisible{% endif %}"
             data-jbs-ms-check
             aria-hidden="true"></i>
          <span>{{ option_label }}</span>
        </button>
      {%- endfor %}
    </div>
    <div data-jbs-ms-hidden>
      {%- for value in selected_values %}
        <input type="hidden" name="{{ input_name }}" value="{{ value }}">
      {%- endfor %}
    </div>
  </div>
{%- endmacro -%}

{%- macro filter_single_select(name, label, options, selected_value="",
                               placeholder=None, auto_submit=True,
                               input_name=None, class_name="", attrs="") -%}
  {%- set selected_values = [selected_value] if selected_value else [] -%}
  {{ filter_multi_select(
    name=name,
    label=label,
    options=options,
    selected_values=selected_values,
    placeholder=placeholder,
    single_select=True,
    auto_submit=auto_submit,
    input_name=input_name,
    class_name=class_name,
    attrs=attrs
  ) }}
{%- endmacro -%}

{%- macro date_range_picker(from_name="from_ts", to_name="to_ts",
                            from_value="", to_value="", label="Date range",
                            button_label="Range",
                            auto_submit=True, class_name="", attrs="",
                            presets=None) -%}
  {%- set presets = presets or [
        {"label": "15m", "minutes": 15},
        {"label": "1h", "minutes": 60},
        {"label": "6h", "minutes": 360},
        {"label": "24h", "minutes": 1440},
        {"label": "7d", "minutes": 10080},
      ] -%}
  {%- set wrapper_classes = "jbs-date-range position-relative" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="{{ wrapper_classes }}"
       data-jbs-date-range
       data-jbs-drp-auto-submit="{{ 'true' if auto_submit else 'false' }}"
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <label class="form-label small text-body-secondary">{{ label }}</label>
    <div class="input-group input-group-sm">
      <input type="text"
             class="form-control"
             name="{{ from_name }}"
             value="{{ from_value }}"
             placeholder="From"
             data-jbs-drp-from>
      <input type="text"
             class="form-control"
             name="{{ to_name }}"
             value="{{ to_value }}"
             placeholder="To"
             data-jbs-drp-to>
      <button type="button"
              class="btn btn-outline-secondary"
              data-jbs-drp-toggle
              aria-expanded="false">
        <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>
        {{ button_label }}
      </button>
    </div>
    <div class="dropdown-menu shadow-sm p-3 mt-1"
         data-jbs-drp-panel
         hidden>
      <div class="d-flex flex-wrap gap-1 mb-3">
        {%- for preset in presets %}
          <button type="button"
                  class="btn btn-outline-secondary btn-sm"
                  data-jbs-drp-preset
                  data-jbs-minutes="{{ preset.minutes }}">
            {{ preset.label }}
          </button>
        {%- endfor %}
      </div>
      <div class="vstack gap-2">
        <div>
          <label class="form-label small text-body-secondary mb-1">From</label>
          <input type="datetime-local"
                 class="form-control form-control-sm"
                 data-jbs-drp-custom-from>
        </div>
        <div>
          <label class="form-label small text-body-secondary mb-1">To</label>
          <input type="datetime-local"
                 class="form-control form-control-sm"
                 data-jbs-drp-custom-to>
        </div>
      </div>
      <div class="d-flex gap-2 mt-3">
        <button type="button"
                class="btn btn-primary btn-sm flex-grow-1"
                data-jbs-drp-apply>
          Apply
        </button>
        <button type="button"
                class="btn btn-outline-secondary btn-sm"
                data-jbs-drp-clear>
          Clear
        </button>
      </div>
    </div>
  </div>
{%- endmacro -%}

{%- macro regex_filter_input(name="q", value="", input_id=None, dropdown_id=None,
                             placeholder="Regex filter (&&, !, \\\\&&)",
                             validate_endpoint=None, hint_text=None,
                             class_name="", attrs="") -%}
  {%- set input_id = input_id or (name ~ "-regex-input") -%}
  {%- set dropdown_id = dropdown_id or (name ~ "-regex-dropdown") -%}
  {%- set assist_classes = "jbs-assist position-relative" -%}
  {%- if class_name -%}
    {%- set assist_classes = assist_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="{{ assist_classes }}"
       data-jbs-assist="regex"
       data-jbs-assist-value-key="query"
       {%- if validate_endpoint %}
         data-jbs-assist-validate-endpoint="{{ validate_endpoint }}"
       {% endif -%}
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <input type="text"
           id="{{ input_id }}"
           name="{{ name }}"
           value="{{ value }}"
           class="form-control form-control-sm font-monospace"
           placeholder="{{ placeholder }}"
           autocomplete="off"
           data-jbs-assist-input
           aria-autocomplete="list"
           aria-expanded="false"
           aria-controls="{{ dropdown_id }}">
    <ul id="{{ dropdown_id }}"
        class="dropdown-menu w-100 shadow-sm mt-1"
        role="listbox"
        data-jbs-assist-panel
        hidden></ul>
    <div class="form-text small" data-jbs-assist-status>
      {{ hint_text or "Use && for AND, ! for negate, \\\\&& for literal &&." }}
    </div>
  </div>
{%- endmacro -%}

{%- macro sql_filter_input(name="sql", value="", input_id=None, dropdown_id=None,
                           placeholder="SQL WHERE expression",
                           hints_endpoint=None, validate_endpoint=None,
                           hint_text=None, class_name="", attrs="") -%}
  {%- set input_id = input_id or (name ~ "-sql-input") -%}
  {%- set dropdown_id = dropdown_id or (name ~ "-sql-dropdown") -%}
  {%- set assist_classes = "jbs-assist position-relative" -%}
  {%- if class_name -%}
    {%- set assist_classes = assist_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="{{ assist_classes }}"
       data-jbs-assist="sql"
       data-jbs-assist-value-key="sql"
       {%- if hints_endpoint %}
         data-jbs-assist-hints-endpoint="{{ hints_endpoint }}"
       {% endif -%}
       {%- if validate_endpoint %}
         data-jbs-assist-validate-endpoint="{{ validate_endpoint }}"
       {% endif -%}
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <input type="text"
           id="{{ input_id }}"
           name="{{ name }}"
           value="{{ value }}"
           class="form-control form-control-sm font-monospace"
           placeholder="{{ placeholder }}"
           autocomplete="off"
           data-jbs-assist-input
           aria-autocomplete="list"
           aria-expanded="false"
           aria-controls="{{ dropdown_id }}">
    <ul id="{{ dropdown_id }}"
        class="dropdown-menu w-100 shadow-sm mt-1"
        role="listbox"
        data-jbs-assist-panel
        hidden></ul>
    <div class="form-text small" data-jbs-assist-status>
      {{ hint_text or "Use field hints and SQL operators to build safe filters." }}
    </div>
  </div>
{%- endmacro -%}

{%- macro form_input(name, label=None, value="", input_type="text", placeholder=None,
                     variant=None, help_text=None, invalid_text=None,
                     valid=False, required=False, class_name="", id=None,
                     attrs="") -%}
  {%- set field_id = id or name -%}
  {%- set input_classes = "form-control" -%}
  {%- if variant -%}
    {%- set input_classes = input_classes ~ " border-" ~ variant -%}
  {%- endif -%}
  {%- if invalid_text -%}
    {%- set input_classes = input_classes ~ " is-invalid" -%}
  {%- elif valid -%}
    {%- set input_classes = input_classes ~ " is-valid" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set input_classes = input_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="mb-3">
    {%- if label %}
      <label for="{{ field_id }}" class="form-label">{{ label }}</label>
    {%- endif %}
    <input
      type="{{ input_type }}"
      name="{{ name }}"
      id="{{ field_id }}"
      value="{{ value }}"
      class="{{ input_classes }}"
      {%- if placeholder %} placeholder="{{ placeholder }}"{% endif -%}
      {%- if required %} required{% endif -%}
      {%- if attrs %} {{ attrs|safe }}{% endif -%}
    >
    {%- if help_text %}
      <div class="form-text">{{ help_text }}</div>
    {%- endif %}
    {%- if invalid_text %}
      <div class="invalid-feedback">{{ invalid_text }}</div>
    {%- endif %}
  </div>
{%- endmacro -%}

{%- macro form_select(name, options, label=None, value="", placeholder=None,
                      help_text=None, invalid_text=None, valid=False,
                      required=False, class_name="", id=None, attrs="") -%}
  {%- set field_id = id or name -%}
  {%- set select_classes = "form-select" -%}
  {%- if invalid_text -%}
    {%- set select_classes = select_classes ~ " is-invalid" -%}
  {%- elif valid -%}
    {%- set select_classes = select_classes ~ " is-valid" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set select_classes = select_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="mb-3">
    {%- if label %}
      <label for="{{ field_id }}" class="form-label">{{ label }}</label>
    {%- endif %}
    <select
      name="{{ name }}"
      id="{{ field_id }}"
      class="{{ select_classes }}"
      {%- if required %} required{% endif -%}
      {%- if attrs %} {{ attrs|safe }}{% endif -%}
    >
      {%- if placeholder is not none %}
        <option value="">{{ placeholder }}</option>
      {%- endif %}
      {%- for option in options %}
        {%- set option_value = (
              option.value if option.value is defined else option[0]
            ) -%}
        {%- set option_label = (
              option.label if option.label is defined else option[1]
            ) -%}
        <option value="{{ option_value }}"
                {%- if option_value|string == value|string %} selected{% endif -%}>
          {{ option_label }}
        </option>
      {%- endfor %}
    </select>
    {%- if help_text %}
      <div class="form-text">{{ help_text }}</div>
    {%- endif %}
    {%- if invalid_text %}
      <div class="invalid-feedback">{{ invalid_text }}</div>
    {%- endif %}
  </div>
{%- endmacro -%}

{%- macro autocomplete(name, endpoint, value="", display_value=None, label=None,
                       placeholder=None, help_text=None, invalid_text=None,
                       valid=False, required=False, min_chars=1,
                       class_name="", input_class="", panel_class="",
                       id=None, attrs="") -%}
  {%- set field_id = id or name -%}
  {%- set display_id = field_id ~ "-display" -%}
  {%- set panel_id = field_id ~ "-panel" -%}
  {%- set display_value = display_value if display_value is not none else value -%}
  {%- set input_classes = "form-control" -%}
  {%- if invalid_text -%}
    {%- set input_classes = input_classes ~ " is-invalid" -%}
  {%- elif valid -%}
    {%- set input_classes = input_classes ~ " is-valid" -%}
  {%- endif -%}
  {%- if input_class -%}
    {%- set input_classes = input_classes ~ " " ~ input_class -%}
  {%- endif -%}
  {%- set wrapper_classes = "jbs-autocomplete position-relative" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set panel_classes = "dropdown-menu w-100 shadow-sm" -%}
  {%- if panel_class -%}
    {%- set panel_classes = panel_classes ~ " " ~ panel_class -%}
  {%- endif -%}
  <div class="{{ wrapper_classes }}"
       data-jbs-autocomplete
       data-jbs-autocomplete-endpoint="{{ endpoint }}"
       data-jbs-autocomplete-min-chars="{{ min_chars }}"
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if label %}
      <label for="{{ display_id }}" class="form-label">{{ label }}</label>
    {%- endif %}
    <input type="text"
           id="{{ display_id }}"
           class="{{ input_classes }}"
           value="{{ display_value }}"
           role="combobox"
           autocomplete="off"
           aria-autocomplete="list"
           aria-expanded="false"
           aria-controls="{{ panel_id }}"
           data-jbs-autocomplete-input
           {%- if placeholder %} placeholder="{{ placeholder }}"{% endif -%}
           {%- if required %} required{% endif -%}>
    <input type="hidden"
           name="{{ name }}"
           id="{{ field_id }}"
           value="{{ value }}"
           data-jbs-autocomplete-value
           data-jbs-autocomplete-selected-label="{{ display_value }}">
    <div id="{{ panel_id }}"
         class="{{ panel_classes }}"
         data-jbs-autocomplete-panel
         role="listbox"
         hidden></div>
    {%- if help_text %}
      <div class="form-text">{{ help_text }}</div>
    {%- endif %}
    {%- if invalid_text %}
      <div class="invalid-feedback d-block">{{ invalid_text }}</div>
    {%- endif %}
  </div>
{%- endmacro -%}

{%- macro textarea(name, label=None, value="", rows=4, placeholder=None,
                   help_text=None, invalid_text=None, valid=False,
                   class_name="", id=None, attrs="") -%}
  {%- set field_id = id or name -%}
  {%- set textarea_classes = "form-control" -%}
  {%- if invalid_text -%}
    {%- set textarea_classes = textarea_classes ~ " is-invalid" -%}
  {%- elif valid -%}
    {%- set textarea_classes = textarea_classes ~ " is-valid" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set textarea_classes = textarea_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="mb-3">
    {%- if label %}
      <label for="{{ field_id }}" class="form-label">{{ label }}</label>
    {%- endif %}
    <textarea
      name="{{ name }}"
      id="{{ field_id }}"
      rows="{{ rows }}"
      class="{{ textarea_classes }}"
      {%- if placeholder %} placeholder="{{ placeholder }}"{% endif -%}
      {%- if attrs %} {{ attrs|safe }}{% endif -%}
    >{{ value }}</textarea>
    {%- if help_text %}
      <div class="form-text">{{ help_text }}</div>
    {%- endif %}
    {%- if invalid_text %}
      <div class="invalid-feedback">{{ invalid_text }}</div>
    {%- endif %}
  </div>
{%- endmacro -%}

{%- macro navbar(brand, brand_href="/", nav_items=None, expand="lg",
                 theme="light", background="light", class_name="", id=None,
                 attrs="") -%}
  {%- set nav_items = nav_items or [] -%}
  {%- set collapse_id = id ~ "-content" if id else "navbarSupportedContent" -%}
  <nav class="navbar navbar-expand-{{ expand }} navbar-{{ theme }} bg-{{ background }}
              {% if class_name %} {{ class_name }}{% endif %}"
       {%- if id %} id="{{ id }}"{% endif -%}
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="container-fluid">
      <a class="navbar-brand" href="{{ brand_href }}">{{ brand }}</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
              data-bs-target="#{{ collapse_id }}" aria-controls="{{ collapse_id }}"
              aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="{{ collapse_id }}">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          {%- for item in nav_items %}
            <li class="nav-item">
              <a class="nav-link{% if item.active %} active{% endif %}"
                 href="{{ item.href }}">{{ item.label }}</a>
            </li>
          {%- endfor %}
        </ul>
      </div>
    </div>
  </nav>
{%- endmacro -%}

{%- macro sort_indicator(active, direction) -%}
  {%- if not active -%}
    <span class="text-body-tertiary" aria-hidden="true">&harr;</span>
  {%- elif direction == "desc" -%}
    <span aria-hidden="true">&darr;</span>
  {%- else -%}
    <span aria-hidden="true">&uarr;</span>
  {%- endif -%}
{%- endmacro -%}

{%- macro table(component_id, endpoint, columns, rows, state=None,
                 total_rows=None, title=None, subtitle=None, toolbar=None,
                 empty_message="No rows found.", persist="memory",
                 state_keys=None, sse_endpoint=None, sse_event="refresh",
                 stream_mode="replace", stream_max_rows=None,
                 stream_pause_when_hidden=False, stream_buffer_max=100,
                 lazy=False,
                 class_name="", attrs="") -%}
  {%- set state = state or {} -%}
  {%- set state_keys = (
        state_keys or ["page", "page_size", "sort_by", "sort_dir", "query"]
      ) -%}
  {%- set page = state.page or 1 -%}
  {%- set page_size = state.page_size or 10 -%}
  {%- set total_rows = total_rows if total_rows is not none else rows|length -%}
  {%- set current_sort_by = state.sort_by or "" -%}
  {%- set current_sort_dir = state.sort_dir or "asc" -%}
  {%- set page_count = ((total_rows - 1) // page_size) + 1 if total_rows > 0 else 1 -%}
  {%- set pause_stream = 'true' if stream_pause_when_hidden else 'false' -%}
  <section id="{{ component_id }}"
           class="card shadow-sm{% if class_name %} {{ class_name }}{% endif %}"
           data-jbs-component="table"
           data-jbs-endpoint="{{ endpoint }}"
           data-jbs-target="#{{ component_id }}"
           data-jbs-key="{{ component_id }}"
           data-jbs-swap="outerHTML"
           data-jbs-persist="{{ persist }}"
           data-jbs-state-keys="{{ state_keys|join(',') }}"
           {%- if sse_endpoint %} data-jbs-sse="{{ sse_endpoint }}"{% endif -%}
           {%- if sse_endpoint %} data-jbs-sse-event="{{ sse_event }}"{% endif -%}
           data-jbs-stream-mode="{{ stream_mode }}"
           {%- if stream_max_rows is not none %}
             data-jbs-stream-max-rows="{{ stream_max_rows }}"
           {% endif -%}
           data-jbs-stream-pause-when-hidden="{{ pause_stream }}"
           data-jbs-stream-buffer-max="{{ stream_buffer_max }}"
           {%- if lazy %} data-jbs-lazy="true"{% endif -%}
           data-jbs-state='{{ state|tojson }}'
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or subtitle or toolbar %}
      <div class="card-header bg-body">
        <div class="d-flex flex-wrap align-items-start
                    justify-content-between gap-3">
          <div>
            {%- if title %}
              <h2 class="h5 mb-1">{{ title }}</h2>
            {%- endif %}
            {%- if subtitle %}
              <p class="text-body-secondary mb-0">{{ subtitle }}</p>
            {%- endif %}
          </div>
          {%- if toolbar %}
            <div class="ms-auto">{{ toolbar|safe }}</div>
          {%- endif %}
        </div>
      </div>
    {%- endif %}
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            {%- for column in columns %}
              <th
                scope="col"
                {%- if column.header_class %}
                  class="{{ column.header_class }}"
                {%- endif %}>
                {%- if column.sortable %}
                  {%- set is_active = current_sort_by == column.key -%}
                  {%- set next_direction = (
                        "desc" if is_active and current_sort_dir == "asc" else "asc"
                      ) -%}
                  <button type="button"
                          class="btn btn-link px-0 py-0
                                 text-decoration-none fw-semibold text-body"
                          data-jbs-action="sort"
                          data-jbs-sort-key="{{ column.key }}"
                          data-jbs-sort-direction="{{ next_direction }}">
                    {{ column.label }}
                    {{ sort_indicator(is_active, current_sort_dir) }}
                  </button>
                {%- else %}
                  {{ column.label }}
                {%- endif %}
              </th>
            {%- endfor %}
          </tr>
        </thead>
        <tbody>
          {%- if rows %}
            {%- for row in rows %}
              <tr{%- if row.id is defined %} data-jbs-row-id="{{ row.id }}"{% endif -%}>
                {%- for column in columns %}
                  {%- set cell = row[column.key] -%}
                  <td
                    {%- if column.cell_class %}
                      class="{{ column.cell_class }}"
                    {%- endif %}>
                    {%- if column.html %}{{ cell|safe }}{% else %}{{ cell }}{% endif %}
                  </td>
                {%- endfor %}
              </tr>
            {%- endfor %}
          {%- else %}
            <tr>
              <td colspan="{{ columns|length }}"
                  class="text-center text-body-secondary py-4">
                {{ empty_message }}
              </td>
            </tr>
          {%- endif %}
        </tbody>
      </table>
    </div>
    <div class="card-footer bg-body d-flex flex-wrap align-items-center
                justify-content-between gap-3">
      <small class="text-body-secondary">
        Showing {{ rows|length }} of {{ total_rows }}
        {{- " result" -}}{%- if total_rows != 1 %}s{% endif %}
      </small>
      <div class="btn-group" role="group" aria-label="Pagination">
        {{ button(
          "Previous",
          variant="outline-secondary",
          size="sm",
          disabled=page <= 1,
          jbs_action="page",
          jbs_page=page - 1
        ) }}
        <span class="btn btn-outline-secondary btn-sm disabled">
          Page {{ page }} of {{ page_count }}
        </span>
        {{ button(
          "Next",
          variant="outline-secondary",
          size="sm",
          disabled=page >= page_count,
          jbs_action="page",
          jbs_page=page + 1
        ) }}
      </div>
    </div>
  </section>
{%- endmacro -%}
"""


def bootstrap_loader(template_name: str = MACRO_TEMPLATE_NAME) -> DictLoader:
    """Return a loader that exposes the packaged Bootstrap macros as a template."""

    return DictLoader({template_name: BOOTSTRAP_MACROS})


def register_bootstrap_macros(
    environment: Environment,
    template_name: str = MACRO_TEMPLATE_NAME,
) -> Environment:
    """Register the macro template in an existing Jinja environment.

    Parameters
    ----------
    environment:
        The environment that should be able to import the packaged macros.
    template_name:
        The virtual template path used in ``{% import %}`` statements.

    Returns
    -------
    Environment
        The same environment instance, updated in place for fluent setup code.
    """

    loader: BaseLoader = bootstrap_loader(template_name)
    if environment.loader is None:
        environment.loader = loader
        return environment

    environment.loader = ChoiceLoader([environment.loader, loader])
    return environment
