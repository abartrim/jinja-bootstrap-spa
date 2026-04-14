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

{%- macro segmented_control(group_id, items, active=None, class_name="", attrs="") -%}
  {%- set classes = "jbs-segmented-control" -%}
  {%- if class_name -%}
    {%- set classes = classes ~ " " ~ class_name -%}
  {%- endif -%}
  {{-
    tabs(
      group_id,
      items,
      active=active,
      variant="pills",
      class_name=classes,
      attrs=attrs
    )
  -}}
{%- endmacro -%}

{%- macro page_header(title=None, subtitle=None, icon=None, eyebrow=None,
                      title_html=None, meta_html=None, actions_html=None,
                      breadcrumbs=None, class_name="", attrs="") -%}
  {%- set breadcrumbs = breadcrumbs or [] -%}
  {%- set wrapper_classes = "jbs-page-header" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section class="{{ wrapper_classes }}"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if breadcrumbs %}
      <nav aria-label="Breadcrumb" class="mb-2">
        <ol class="breadcrumb mb-0 small">
          {%- for crumb in breadcrumbs %}
            {%- set crumb_label = (
                  crumb.label if crumb.label is defined
                  else (crumb["label"] if crumb is mapping else crumb)
                ) -%}
            {%- set crumb_href = (
                  crumb.href if crumb.href is defined
                  else (crumb["href"] if crumb is mapping and "href" in crumb else none)
                ) -%}
            {%- set crumb_active = (
                  crumb.active if crumb.active is defined
                  else (
                    crumb["active"]
                    if crumb is mapping and "active" in crumb
                    else loop.last
                  )
                ) -%}
            <li class="breadcrumb-item{% if crumb_active %} active{% endif %}"
                {%- if crumb_active %} aria-current="page"{% endif -%}>
              {%- if crumb_href and not crumb_active %}
                <a href="{{ crumb_href }}">{{ crumb_label }}</a>
              {%- else %}
                {{ crumb_label }}
              {%- endif %}
            </li>
          {%- endfor %}
        </ol>
      </nav>
    {%- endif %}
    <div class="d-flex flex-wrap align-items-start justify-content-between gap-3">
      <div class="min-w-0">
        {%- if eyebrow %}
          <div class="text-uppercase small fw-semibold text-body-secondary mb-1">
            {{ eyebrow }}
          </div>
        {%- endif %}
        {%- if title_html %}
          {{ title_html|safe }}
        {%- elif title %}
          <h1 class="h3 mb-1 d-flex align-items-center gap-2">
            {%- if icon %}
              <i class="{{ icon }}" aria-hidden="true"></i>
            {%- endif %}
            <span>{{ title }}</span>
          </h1>
        {%- endif %}
        {%- if subtitle %}
          <p class="text-body-secondary mb-0">{{ subtitle }}</p>
        {%- endif %}
      </div>
      {%- if meta_html or actions_html %}
        <div class="d-flex flex-wrap align-items-center
                    justify-content-end gap-2 ms-auto">
          {%- if meta_html %}
            <div class="d-flex flex-wrap align-items-center gap-2">
              {{ meta_html|safe }}
            </div>
          {%- endif %}
          {%- if actions_html %}
            <div class="d-flex flex-wrap align-items-center gap-2">
              {{ actions_html|safe }}
            </div>
          {%- endif %}
        </div>
      {%- endif %}
    </div>
  </section>
{%- endmacro -%}

{%- macro toolbar(toolbar_id=None, title=None, subtitle=None, body="",
                  badges=None, actions_html=None, collapsible=False,
                  expanded=True, class_name="", attrs="") -%}
  {%- set badges = badges or [] -%}
  {%- set wrapper_classes = "card border-secondary shadow-sm jbs-toolbar" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set panel_id = toolbar_id ~ "-panel" if toolbar_id else none -%}
  {%- set trigger_id = toolbar_id ~ "-trigger" if toolbar_id else none -%}
  {%- set content = caller() if caller is defined else body -%}
  <section
    class="{{ wrapper_classes }}"
    {%- if toolbar_id %} id="{{ toolbar_id }}"{% endif -%}
    {%- if collapsible %} data-jbs-disclosure{% endif -%}
    {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="card-header bg-body py-2">
      <div class="d-flex flex-wrap align-items-start justify-content-between gap-3">
        <div class="min-w-0">
          {%- if title %}
            <h2 class="h6 mb-1">{{ title }}</h2>
          {%- endif %}
          {%- if subtitle %}
            <p class="text-body-secondary small mb-0">{{ subtitle }}</p>
          {%- endif %}
          {%- if badges %}
            <div class="d-flex flex-wrap align-items-center gap-2 mt-2">
              {%- for badge in badges %}
                {%- set badge_label = (
                      badge.label if badge.label is defined
                      else (
                        badge["label"]
                        if badge is mapping and "label" in badge
                        else badge
                      )
                    ) -%}
                {%- set badge_variant = (
                      badge.variant if badge.variant is defined
                      else (
                        badge["variant"]
                        if badge is mapping and "variant" in badge
                        else "secondary"
                      )
                    ) -%}
                {%- set badge_class_name = (
                      badge.class_name if badge.class_name is defined
                      else (
                        badge["class_name"]
                        if badge is mapping and "class_name" in badge
                        else ""
                      )
                    ) -%}
                {%- set badge_classes = "badge text-bg-" ~ badge_variant -%}
                {%- if badge_class_name -%}
                  {%- set badge_classes = badge_classes ~ " " ~ badge_class_name -%}
                {%- endif -%}
                <span class="{{ badge_classes }}">
                  {{ badge_label }}
                </span>
              {%- endfor %}
            </div>
          {%- endif %}
        </div>
        {%- if actions_html or collapsible %}
          <div class="d-flex flex-wrap align-items-center
                      justify-content-end gap-2 ms-auto">
            {%- if actions_html %}
              {{ actions_html|safe }}
            {%- endif %}
            {%- if collapsible %}
              <button type="button"
                      class="btn btn-sm btn-outline-secondary"
                      {%- if trigger_id %} id="{{ trigger_id }}"{% endif -%}
                      data-jbs-disclosure-trigger
                      aria-expanded="{{ 'true' if expanded else 'false' }}"
                      {%- if panel_id %} aria-controls="{{ panel_id }}"{% endif -%}>
                <span>{{ "Hide" if expanded else "Show" }}</span>
                <span class="ms-1" data-jbs-disclosure-icon aria-hidden="true">
                  <i class="bi bi-chevron-down"></i>
                </span>
              </button>
            {%- endif %}
          </div>
        {%- endif %}
      </div>
    </div>
    <div class="card-body"
         {%- if panel_id %} id="{{ panel_id }}"{% endif -%}
         {%- if collapsible %} data-jbs-disclosure-panel{% endif -%}
         {%- if collapsible and trigger_id %}
           aria-labelledby="{{ trigger_id }}"
         {% endif -%}
         {%- if collapsible and not expanded %} hidden{% endif -%}>
      {{ content|safe }}
    </div>
  </section>
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

{%- macro stat_card(title, value, subtitle=None, icon=None, tone="primary",
                    href=None, trend=None, class_name="", attrs="") -%}
  {%- set tag = "a" if href else "article" -%}
  {%- set wrapper_classes = "card shadow-sm h-100 text-decoration-none
                             jbs-stat-card" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set trend_label = (
        trend.label if trend is defined and trend and trend.label is defined
        else (
          trend["label"]
          if trend is mapping and "label" in trend
          else trend
        )
      ) -%}
  {%- set trend_tone = (
        trend.tone if trend is defined and trend and trend.tone is defined
        else (
          trend["tone"]
          if trend is mapping and "tone" in trend
          else tone
        )
      ) -%}
  <{{ tag }} class="{{ wrapper_classes }}"
    {%- if href %} href="{{ href }}"{% endif -%}
    {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="card-body">
      <div class="d-flex align-items-start justify-content-between gap-3">
        <div class="min-w-0">
          <div class="text-uppercase small fw-semibold text-body-secondary mb-2">
            {{ title }}
          </div>
          <div class="display-6 fw-semibold mb-1">{{ value }}</div>
          {%- if subtitle %}
            <p class="text-body-secondary mb-0">{{ subtitle }}</p>
          {%- endif %}
        </div>
        {%- if icon %}
          <span class="badge rounded-pill text-bg-{{ tone }}">
            <i class="{{ icon }}" aria-hidden="true"></i>
          </span>
        {%- endif %}
      </div>
    </div>
    {%- if trend_label %}
      <div class="card-footer bg-body border-0 pt-0">
        <span class="badge text-bg-{{ trend_tone }}">
          {{ trend_label }}
        </span>
      </div>
    {%- endif %}
  </{{ tag }}>
{%- endmacro -%}

{%- macro empty_state(title, message, icon=None, action_html=None, compact=False,
                      class_name="", attrs="") -%}
  {%- set wrapper_classes = "jbs-empty-state text-center border rounded-3
                             bg-body-tertiary" -%}
  {%- if compact -%}
    {%- set wrapper_classes = wrapper_classes ~ " p-3" -%}
  {%- else -%}
    {%- set wrapper_classes = wrapper_classes ~ " p-4 p-lg-5" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section class="{{ wrapper_classes }}"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if icon %}
      <div class="mb-3 text-body-secondary fs-2">
        <i class="{{ icon }}" aria-hidden="true"></i>
      </div>
    {%- endif %}
    <h3 class="{% if compact %}h6{% else %}h5{% endif %} mb-2">{{ title }}</h3>
    <p class="text-body-secondary mb-{% if action_html %}3{% else %}0{% endif %}">
      {{ message }}
    </p>
    {%- if action_html %}
      <div class="d-flex flex-wrap align-items-center justify-content-center gap-2">
        {{ action_html|safe }}
      </div>
    {%- endif %}
  </section>
{%- endmacro -%}

{%- macro detail_list(items, columns=1, striped=False, compact=False,
                      class_name="", attrs="") -%}
  {%- set items = items or [] -%}
  {%- set wrapper_classes = "row g-3 jbs-detail-list" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- if columns|int <= 1 -%}
    {%- set item_column_class = "col-12" -%}
  {%- elif columns|int == 2 -%}
    {%- set item_column_class = "col-12 col-lg-6" -%}
  {%- else -%}
    {%- set item_column_class = "col-12 col-md-6 col-xl-4" -%}
  {%- endif -%}
  <div class="{{ wrapper_classes }}"
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- for item in items %}
      {%- set item_label = (
            item.label if item.label is defined
            else (item["label"] if item is mapping else "")
          ) -%}
      {%- set item_value = (
            item.value if item.value is defined
            else (
              item["value"]
              if item is mapping and "value" in item
              else none
            )
          ) -%}
      {%- set item_value_html = (
            item.value_html if item.value_html is defined
            else (
              item["value_html"]
              if item is mapping and "value_html" in item
              else none
            )
          ) -%}
      {%- set item_class_name = (
            item.class_name if item.class_name is defined
            else (
              item["class_name"]
              if item is mapping and "class_name" in item
              else ""
            )
          ) -%}
      <div class="{{ item_column_class }}">
        <div class="border rounded-3 h-100
                    {% if compact %} p-2{% else %} p-3{% endif %}
                    {% if striped and
                          loop.index0 % 2 == 1 %} bg-body-tertiary{% endif %}
                    {% if item_class_name %} {{ item_class_name }}{% endif %}">
          <dt class="text-uppercase small text-body-secondary mb-1">
            {{ item_label }}
          </dt>
          <dd class="mb-0">
            {%- if item_value_html %}
              {{ item_value_html|safe }}
            {% else %}
              <span class="fw-semibold">{{ item_value }}</span>
            {% endif -%}
          </dd>
        </div>
      </div>
    {%- endfor %}
  </div>
{%- endmacro -%}

{%- macro key_value_panel(items, columns=1, striped=False, compact=False,
                          class_name="", attrs="") -%}
  {{-
    detail_list(
      items=items,
      columns=columns,
      striped=striped,
      compact=compact,
      class_name=class_name,
      attrs=attrs
    )
  -}}
{%- endmacro -%}

{%- macro callout(title=None, message="", message_html=None, tone="info",
                  icon=None, dismissible=False, class_name="", attrs="") -%}
  {%- set wrapper_classes = "alert alert-" ~ tone ~ " shadow-sm jbs-callout" -%}
  {%- if dismissible -%}
    {%- set wrapper_classes = wrapper_classes ~ " alert-dismissible" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <aside class="{{ wrapper_classes }}"
         role="note"
         {%- if dismissible %} data-jbs-status-region{% endif -%}
         {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="d-flex align-items-start gap-3">
      {%- if icon %}
        <div class="fs-5">
          <i class="{{ icon }}" aria-hidden="true"></i>
        </div>
      {%- endif %}
      <div class="min-w-0 flex-grow-1">
        {%- if title %}
          <h3 class="h6 mb-1">{{ title }}</h3>
        {%- endif %}
        <div>
          {%- if message_html %}
            {{ message_html|safe }}
          {% else %}
            {{ message }}
          {% endif -%}
        </div>
      </div>
      {%- if dismissible %}
        <button type="button"
                class="btn-close"
                aria-label="Dismiss"
                data-jbs-status-dismiss></button>
      {%- endif %}
    </div>
  </aside>
{%- endmacro -%}

{%- macro chart_shell(chart_id, title=None, subtitle=None, badges=None,
                      actions_html=None, footer_html=None, empty_html=None,
                      error_html=None, class_name="", attrs="") -%}
  {%- set badges = badges or [] -%}
  {%- set wrapper_classes = "card shadow-sm jbs-chart-shell" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set body_html = caller() if caller is defined else none -%}
  <section id="{{ chart_id }}"
           class="{{ wrapper_classes }}"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="card-header bg-body">
      <div class="d-flex flex-wrap align-items-start justify-content-between gap-3">
        <div class="min-w-0">
          {%- if title %}
            <h3 class="h5 mb-1">{{ title }}</h3>
          {%- endif %}
          {%- if subtitle %}
            <p class="text-body-secondary mb-0">{{ subtitle }}</p>
          {%- endif %}
          {%- if badges %}
            <div class="d-flex flex-wrap align-items-center gap-2 mt-2">
              {%- for badge in badges %}
                {%- set badge_label = (
                      badge.label if badge.label is defined
                      else (
                        badge["label"]
                        if badge is mapping and "label" in badge
                        else badge
                      )
                    ) -%}
                {%- set badge_variant = (
                      badge.variant if badge.variant is defined
                      else (
                        badge["variant"]
                        if badge is mapping and "variant" in badge
                        else "secondary"
                      )
                    ) -%}
                <span class="badge text-bg-{{ badge_variant }}">{{ badge_label }}</span>
              {%- endfor %}
            </div>
          {%- endif %}
        </div>
        {%- if actions_html %}
          <div class="ms-auto d-flex flex-wrap align-items-center gap-2">
            {{ actions_html|safe }}
          </div>
        {%- endif %}
      </div>
    </div>
    <div class="card-body">
      {%- if body_html %}
        {{ body_html|safe }}
      {%- elif empty_html %}
        {{ empty_html|safe }}
      {%- else %}
        <div class="ratio ratio-16x9 border rounded-3 bg-body-tertiary">
          <div class="d-flex align-items-center justify-content-center
                      text-body-secondary">
            Chart render target
          </div>
        </div>
      {%- endif %}
      {%- if empty_html %}
        <div class="d-none" data-jbs-empty-template>{{ empty_html|safe }}</div>
      {%- endif %}
      {%- if error_html %}
        <div class="d-none" data-jbs-error-template>{{ error_html|safe }}</div>
      {%- endif %}
    </div>
    {%- if footer_html %}
      <div class="card-footer bg-body">{{ footer_html|safe }}</div>
    {%- endif %}
  </section>
{%- endmacro -%}

{%- macro split_panel(direction="horizontal", ratio="1/1",
                      collapse_on_mobile=True, class_name="", attrs="") -%}
  {%- set ratio_parts = ratio.split("/") if "/" in ratio else ["1", "1"] -%}
  {%- set primary_size = ratio_parts[0]|trim if ratio_parts|length > 0 else "1" -%}
  {%- set secondary_size = ratio_parts[1]|trim if ratio_parts|length > 1 else "1" -%}
  {%- set wrapper_classes = "jbs-split-panel" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section class="{{ wrapper_classes }}"
           data-jbs-split-panel
           data-jbs-direction="{{ direction }}"
           data-jbs-collapse-on-mobile="{{ 'true' if collapse_on_mobile else 'false' }}"
           style="--jbs-split-primary: minmax(0, {{ primary_size }}fr);
                  --jbs-split-secondary: minmax(0, {{ secondary_size }}fr);"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {{ caller() if caller is defined else "" }}
  </section>
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

{%- macro workspace_modal(overlay_id, title=None, body="", footer_html=None,
                          size="xl", sticky_header=True, sticky_footer=True,
                          close_label="Close", class_name="", attrs="") -%}
  {%- set dialog_classes = "card shadow-lg border-0 w-100 jbs-workspace-modal" -%}
  {%- if size == "lg" -%}
    {%- set dialog_classes = dialog_classes ~ " col-12 col-xl-10" -%}
  {%- elif size == "xxl" -%}
    {%- set dialog_classes = dialog_classes ~ " col-12" -%}
  {%- else -%}
    {%- set dialog_classes = dialog_classes ~ " col-12 col-xxl-11" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set dialog_classes = dialog_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set content = caller() if caller is defined else body -%}
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
                    justify-content-between gap-3
                    {% if sticky_header %} position-sticky top-0 z-1{% endif %}">
          <div class="min-w-0">
            {%- if title %}
              <h2 class="h4 mb-0">{{ title }}</h2>
            {%- endif %}
          </div>
          <button type="button"
                  class="btn btn-sm btn-outline-secondary"
                  data-jbs-overlay-close>
            {{ close_label }}
          </button>
        </div>
        <div class="card-body overflow-auto" style="max-height: min(75vh, 960px);">
          {{ content|safe }}
        </div>
        {%- if footer_html %}
          <div class="card-footer bg-body
                      {% if sticky_footer %} position-sticky bottom-0 z-1{% endif %}">
            {{ footer_html|safe }}
          </div>
        {%- endif %}
      </div>
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

{%- macro toast(toast_id=None, title=None, message="", variant="info",
                dismissible=True, class_name="", attrs="") -%}
  {%- set toast_classes = "alert alert-" ~ variant ~ " shadow-sm mb-0" -%}
  {%- if class_name -%}
    {%- set toast_classes = toast_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <aside class="{{ toast_classes }}"
         role="status"
         aria-live="polite"
         data-jbs-status-region
         {%- if toast_id %} id="{{ toast_id }}"{% endif -%}
         {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="d-flex align-items-start justify-content-between gap-3">
      <div>
        {%- if title %}
          <h3 class="h6 mb-1">{{ title }}</h3>
        {%- endif %}
        <div>{{ message }}</div>
      </div>
      {%- if dismissible %}
        <button type="button"
                class="btn-close"
                aria-label="Dismiss"
                data-jbs-status-dismiss></button>
      {%- endif %}
    </div>
  </aside>
{%- endmacro -%}

{%- macro stream_status(status_id=None, state="idle", label=None, buffered_count=0,
                        updated_at=None, controls_html=None, compact=False,
                        class_name="", attrs="") -%}
  {%- if state == "live" -%}
    {%- set variant = "success" -%}
  {%- elif state == "connecting" -%}
    {%- set variant = "info" -%}
  {%- elif state == "paused" or state == "buffered" -%}
    {%- set variant = "warning" -%}
  {%- elif state == "error" -%}
    {%- set variant = "danger" -%}
  {%- elif state == "stale" -%}
    {%- set variant = "secondary" -%}
  {%- else -%}
    {%- set variant = "secondary" -%}
  {%- endif -%}
  {%- set wrapper_classes = "alert alert-" ~ variant ~ " mb-0 jbs-stream-status" -%}
  {%- if compact -%}
    {%- set wrapper_classes = wrapper_classes ~ " py-2 px-3" -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section class="{{ wrapper_classes }}"
           role="status"
           aria-live="polite"
           data-jbs-stream-status
           data-jbs-stream-state="{{ state }}"
           {%- if status_id %} id="{{ status_id }}"{% endif -%}
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3">
      <div class="d-flex flex-wrap align-items-center gap-2">
        <span class="fw-semibold">{{ label or state|replace("_", " ")|title }}</span>
        {%- if buffered_count %}
          <span class="badge text-bg-dark">{{ buffered_count }} buffered</span>
        {%- endif %}
        {%- if updated_at %}
          <span class="small text-body-secondary">Updated {{ updated_at }}</span>
        {%- endif %}
      </div>
      {%- if controls_html %}
        <div class="d-flex flex-wrap align-items-center gap-2">
          {{ controls_html|safe }}
        </div>
      {%- endif %}
    </div>
  </section>
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
          <span class="ms-auto d-inline-flex align-items-center">
            {{ header_suffix|safe }}
          </span>
        {%- endif %}
        <span class="ms-2" data-jbs-disclosure-icon aria-hidden="true">
          <i class="bi bi-chevron-down"></i>
        </span>
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
    <span class="text-body-tertiary" aria-hidden="true">
      <i class="bi bi-arrow-down-up"></i>
    </span>
  {%- elif direction == "desc" -%}
    <span aria-hidden="true"><i class="bi bi-arrow-down"></i></span>
  {%- else -%}
    <span aria-hidden="true"><i class="bi bi-arrow-up"></i></span>
  {%- endif -%}
{%- endmacro -%}

{%- macro data_grid(component_id, endpoint, columns, rows, state=None,
                    caption=None, subtitle=None, count_label=None,
                    empty_html=None, loading_html=None, error_html=None,
                    toolbar_html=None, row_actions_slot=False,
                    mobile_labels=True, persist="header", state_keys=None,
                    sse_endpoint=None, sse_event="refresh",
                    stream_mode="replace", stream_max_rows=None,
                    stream_pause_when_hidden=False, stream_buffer_max=100,
                    lazy=False, class_name="", attrs="") -%}
  {%- set state = state or {} -%}
  {%- set state_keys = (
        state_keys or ["page", "page_size", "sort_by", "sort_dir", "query"]
      ) -%}
  {%- set page = state.page or 1 -%}
  {%- set page_size = state.page_size or 10 -%}
  {%- set total_rows = rows|length -%}
  {%- set current_sort_by = state.sort_by or "" -%}
  {%- set current_sort_dir = state.sort_dir or "asc" -%}
  {%- set page_count = ((total_rows - 1) // page_size) + 1 if total_rows > 0 else 1 -%}
  {%- set pause_stream = 'true' if stream_pause_when_hidden else 'false' -%}
  {%- set wrapper_classes = "card shadow-sm jbs-data-grid" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set resolved_empty_html = empty_html or empty_state(
        "No results",
        "Try adjusting the current filters or source query.",
        icon="bi bi-inbox",
        compact=True
      ) -%}
  {%- set resolved_loading_html = loading_html or
        '<div class="d-flex align-items-center gap-2">
           <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
           <span>Refreshing grid…</span>
         </div>' -%}
  {%- set resolved_error_html = error_html or callout(
        title="Grid refresh failed",
        message="The server could not return fresh rows.",
        tone="danger",
        icon="bi bi-exclamation-triangle"
      ) -%}
  <section id="{{ component_id }}"
           class="{{ wrapper_classes }}"
           data-jbs-component="table"
           data-jbs-endpoint="{{ endpoint }}"
           data-jbs-target="#{{ component_id }}"
           data-jbs-key="{{ component_id }}"
           data-jbs-swap="outerHTML"
           data-jbs-persist="{{ persist }}"
           data-jbs-state-keys="{{ state_keys|join(',') }}"
           data-jbs-mobile-labels="{{ 'true' if mobile_labels else 'false' }}"
           data-jbs-row-actions-slot="{{ 'true' if row_actions_slot else 'false' }}"
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
    <div class="card-header bg-body">
      <div class="d-flex flex-wrap align-items-start justify-content-between gap-3">
        <div class="min-w-0">
          {%- if caption %}
            <h3 class="h5 mb-1">{{ caption }}</h3>
          {%- endif %}
          {%- if subtitle %}
            <p class="text-body-secondary mb-0">{{ subtitle }}</p>
          {%- endif %}
        </div>
        {%- if toolbar_html %}
          <div class="ms-auto d-flex flex-wrap align-items-center gap-2">
            {{ toolbar_html|safe }}
          </div>
        {%- endif %}
      </div>
    </div>
    <div class="card-body p-0">
      {%- if rows %}
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                {%- for column in columns %}
                  <th scope="col"
                      {%- if column.header_class %}
                        class="{{ column.header_class }}"
                      {%- endif %}>
                    {%- if column.sortable %}
                      {%- set is_active = current_sort_by == column.key -%}
                      {%- set next_direction = (
                            "desc" if is_active and current_sort_dir == "asc" else "asc"
                          ) -%}
                      <button type="button"
                              class="btn btn-link px-0 py-0 text-decoration-none
                                     fw-semibold text-body"
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
              {%- for row in rows %}
                <tr
                  {%- if row.id is defined %}
                    data-jbs-row-id="{{ row.id }}"
                  {% endif -%}>
                  {%- for column in columns %}
                    {%- set cell = row[column.key] -%}
                    <td
                      {%- if column.cell_class %}
                        class="{{ column.cell_class }}"
                      {%- endif %}>
                      {%- if column.html %}
                        {{ cell|safe }}
                      {% else %}
                        {{ cell }}
                      {% endif -%}
                    </td>
                  {%- endfor %}
                </tr>
              {%- endfor %}
            </tbody>
          </table>
        </div>
      {%- else %}
        <div class="p-3 p-lg-4">
          {{ resolved_empty_html|safe }}
        </div>
      {%- endif %}
      <div class="d-none" data-jbs-loading-template>
        {{ resolved_loading_html|safe }}
      </div>
      <div class="d-none" data-jbs-error-template>{{ resolved_error_html|safe }}</div>
      <div class="d-none" data-jbs-empty-template>{{ resolved_empty_html|safe }}</div>
    </div>
    <div class="card-footer bg-body d-flex flex-wrap align-items-center
                justify-content-between gap-3">
      <small class="text-body-secondary">
        {{ count_label or ('Showing ' ~ rows|length ~ ' of ' ~ total_rows ~ ' rows') }}
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

{%- macro searchable_expandable_list(list_id, items, search_input=True,
                                     search_placeholder="Search items...",
                                     empty_title="No matching items",
                                     empty_message="Try another search term.",
                                     class_name="", attrs="") -%}
  {%- set items = items or [] -%}
  {%- set wrapper_classes = "card shadow-sm jbs-searchable-list" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section id="{{ list_id }}"
           class="{{ wrapper_classes }}"
           data-jbs-searchable-list
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if search_input %}
      <div class="card-header bg-body">
        <label class="form-label small text-body-secondary mb-2"
               for="{{ list_id }}-search">
          Search
        </label>
        <input id="{{ list_id }}-search"
               type="search"
               class="form-control form-control-sm"
               placeholder="{{ search_placeholder }}"
               data-jbs-searchable-list-input>
      </div>
    {%- endif %}
    <div class="card-body vstack gap-3">
      {%- for item in items %}
        {%- set item_label = (
              item.label if item.label is defined
              else (item["label"] if item is mapping else "")
            ) -%}
        {%- set item_summary = (
              item.summary if item.summary is defined
              else (
                item["summary"]
                if item is mapping and "summary" in item
                else none
              )
            ) -%}
        {%- set item_search_text = (
              item.search_text if item.search_text is defined
              else (
                item["search_text"]
                if item is mapping and "search_text" in item
                else item_label ~ " " ~ (item_summary or "")
              )
            ) -%}
        {%- set item_tags = (
              item.tags if item.tags is defined
              else (
                item["tags"]
                if item is mapping and "tags" in item
                else []
              )
            ) -%}
        {%- set item_open = (
              item.open if item.open is defined
              else (
                item["open"]
                if item is mapping and "open" in item
                else false
              )
            ) -%}
        {%- set item_panel_id = list_id ~ "-item-" ~ loop.index -%}
        <section class="border rounded-3 overflow-hidden"
                 data-jbs-searchable-item
                 data-jbs-searchable-text="{{ item_search_text|lower }}">
          <div data-jbs-disclosure>
            <button type="button"
                    class="btn btn-link text-start text-decoration-none
                           w-100 px-3 py-3 text-body"
                    data-jbs-disclosure-trigger
                    aria-expanded="{{ 'true' if item_open else 'false' }}"
                    aria-controls="{{ item_panel_id }}">
              <span class="d-flex flex-wrap align-items-start
                           justify-content-between gap-3 w-100">
                <span class="min-w-0">
                  <span class="fw-semibold d-block">{{ item_label }}</span>
                  {%- if item_summary %}
                    <span class="small text-body-secondary d-block mt-1">
                      {{ item_summary }}
                    </span>
                  {%- endif %}
                  {%- if item_tags %}
                    <span class="d-flex flex-wrap gap-1 mt-2">
                      {%- for tag in item_tags %}
                        <span class="badge text-bg-light border">{{ tag }}</span>
                      {%- endfor %}
                    </span>
                  {%- endif %}
                </span>
                <span class="ms-auto text-body-secondary"
                      data-jbs-disclosure-icon
                      aria-hidden="true">
                  <i class="bi bi-chevron-down"></i>
                </span>
              </span>
            </button>
            <div id="{{ item_panel_id }}"
                 class="border-top px-3 py-3"
                 data-jbs-disclosure-panel
                 role="region"
                 {%- if not item_open %} hidden{% endif -%}>
              {%- if caller is defined %}
                {{ caller(item) }}
              {%- else %}
                {{
                  item.body_html|safe
                  if item.body_html is defined
                  else ""
                }}
              {%- endif %}
            </div>
          </div>
        </section>
      {%- endfor %}
      <div data-jbs-searchable-list-empty{% if items %} hidden{% endif %}>
        {{
          empty_state(
            empty_title,
            empty_message,
            icon="bi bi-search",
            compact=True
          )
        }}
      </div>
    </div>
  </section>
{%- endmacro -%}

{%- macro stacked_list(list_id, items, title=None, subtitle=None, flush=True,
                        class_name="", attrs="") -%}
  {%- set items = items or [] -%}
  {%- set wrapper_classes = "card shadow-sm jbs-stacked-list" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section id="{{ list_id }}"
           class="{{ wrapper_classes }}"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or subtitle %}
      <div class="card-header bg-body">
        {%- if title %}
          <h2 class="h6 mb-1">{{ title }}</h2>
        {%- endif %}
        {%- if subtitle %}
          <p class="text-body-secondary mb-0">{{ subtitle }}</p>
        {%- endif %}
      </div>
    {%- endif %}
    <div class="list-group{% if flush %} list-group-flush{% endif %}">
      {%- for item in items %}
        {%- set item_title = (
              item.title if item.title is defined
              else (
                item["title"]
                if item is mapping and "title" in item
                else item.label if item.label is defined
                else (item["label"] if item is mapping and "label" in item else "")
              )
            ) -%}
        {%- set item_subtitle = (
              item.subtitle if item.subtitle is defined
              else (
                item["subtitle"]
                if item is mapping and "subtitle" in item
                else none
              )
            ) -%}
        {%- set item_meta = (
              item.meta if item.meta is defined
              else (
                item["meta"]
                if item is mapping and "meta" in item
                else none
              )
            ) -%}
        {%- set item_href = (
              item.href if item.href is defined
              else (
                item["href"]
                if item is mapping and "href" in item
                else none
              )
            ) -%}
        {%- set item_active = (
              item.active if item.active is defined
              else (
                item["active"]
                if item is mapping and "active" in item
                else false
              )
            ) -%}
        {%- set item_badges = (
              item.badges if item.badges is defined
              else (
                item["badges"]
                if item is mapping and "badges" in item
                else []
              )
            ) -%}
        {%- set item_actions_html = (
              item.actions_html if item.actions_html is defined
              else (
                item["actions_html"]
                if item is mapping and "actions_html" in item
                else none
              )
            ) -%}
        {%- set item_body_html = (
              item.body_html if item.body_html is defined
              else (
                item["body_html"]
                if item is mapping and "body_html" in item
                else none
              )
            ) -%}
        {%- set item_classes = "list-group-item px-3 py-3" -%}
        {%- if item_active -%}
          {%- set item_classes = item_classes ~ " active" -%}
        {%- endif -%}
        <article class="{{ item_classes }}">
          <div class="d-flex flex-wrap align-items-start justify-content-between gap-3">
            <div class="min-w-0 flex-grow-1">
              <div class="d-flex flex-wrap align-items-center gap-2">
                    {%- if item_href %}
                      <a href="{{ item_href }}"
                         class="fw-semibold{% if item_active %} text-white{% else %}
                                link-body-emphasis text-decoration-none{% endif %}">
                        {{ item_title }}
                      </a>
                {%- else %}
                  <span class="fw-semibold">{{ item_title }}</span>
                {%- endif %}
                {%- for badge in item_badges %}
                  {%- set badge_label = (
                        badge.label if badge.label is defined
                        else (
                          badge["label"]
                          if badge is mapping and "label" in badge
                          else badge
                        )
                      ) -%}
                  {%- set badge_variant = (
                        badge.variant if badge.variant is defined
                        else (
                          badge["variant"]
                          if badge is mapping and "variant" in badge
                          else "light"
                        )
                      ) -%}
                      <span class="badge text-bg-{{ badge_variant }}">
                        {{ badge_label }}
                      </span>
                {%- endfor %}
              </div>
              {%- if item_subtitle %}
                    <p class="small mb-0 mt-1
                              {% if item_active %}text-white-50{% else %}
                                text-body-secondary{% endif %}">
                      {{ item_subtitle }}
                    </p>
              {%- endif %}
              {%- if caller is defined %}
                <div class="mt-2{% if item_active %} text-white{% endif %}">
                  {{ caller(item) }}
                </div>
              {%- elif item_body_html %}
                <div class="mt-2{% if item_active %} text-white{% endif %}">
                  {{ item_body_html|safe }}
                </div>
              {%- endif %}
            </div>
            {%- if item_meta or item_actions_html %}
              <div class="d-flex flex-column align-items-end gap-2 ms-auto">
                {%- if item_meta %}
                      <span class="small{% if item_active %} text-white-50{% else %}
                                   text-body-secondary{% endif %}">
                        {{ item_meta }}
                      </span>
                {%- endif %}
                {%- if item_actions_html %}
                  <div>{{ item_actions_html|safe }}</div>
                {%- endif %}
              </div>
            {%- endif %}
          </div>
        </article>
      {%- endfor %}
    </div>
  </section>
{%- endmacro -%}

{%- macro timeline(timeline_id, items, title=None, subtitle=None,
                    class_name="", attrs="") -%}
  {%- set items = items or [] -%}
  {%- set wrapper_classes = "card shadow-sm jbs-timeline" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section id="{{ timeline_id }}"
           class="{{ wrapper_classes }}"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or subtitle %}
      <div class="card-header bg-body">
        {%- if title %}
          <h2 class="h6 mb-1">{{ title }}</h2>
        {%- endif %}
        {%- if subtitle %}
          <p class="text-body-secondary mb-0">{{ subtitle }}</p>
        {%- endif %}
      </div>
    {%- endif %}
    <div class="card-body">
      <ol class="list-unstyled mb-0">
        {%- for item in items %}
          {%- set item_title = (
                item.title if item.title is defined
                else (
                  item["title"]
                  if item is mapping and "title" in item
                  else ""
                )
              ) -%}
          {%- set item_time = (
                item.time if item.time is defined
                else (
                  item["time"]
                  if item is mapping and "time" in item
                  else none
                )
              ) -%}
          {%- set item_body = (
                item.body if item.body is defined
                else (
                  item["body"]
                  if item is mapping and "body" in item
                  else none
                )
              ) -%}
          {%- set item_tone = (
                item.tone if item.tone is defined
                else (
                  item["tone"]
                  if item is mapping and "tone" in item
                  else "primary"
                )
              ) -%}
          {%- set item_icon = (
                item.icon if item.icon is defined
                else (
                  item["icon"]
                  if item is mapping and "icon" in item
                  else "bi bi-record-circle"
                )
              ) -%}
          {%- set item_meta = (
                item.meta if item.meta is defined
                else (
                  item["meta"]
                  if item is mapping and "meta" in item
                  else none
                )
              ) -%}
              <li class="d-flex align-items-start gap-3
                         {% if not loop.last %}pb-4{% endif %}">
            <span class="flex-shrink-0 d-inline-flex align-items-center
                         justify-content-center rounded-circle border border-2
                         border-{{ item_tone }} text-{{ item_tone }}"
                  style="width: 2.25rem; height: 2.25rem;">
              <i class="{{ item_icon }}" aria-hidden="true"></i>
            </span>
                <div class="flex-grow-1 border-start ps-3
                            {% if not loop.last %}pb-2{% endif %}">
                  <div class="d-flex flex-wrap align-items-center
                              justify-content-between gap-2">
                <span class="fw-semibold">{{ item_title }}</span>
                {%- if item_time %}
                  <time class="small text-body-secondary">{{ item_time }}</time>
                {%- endif %}
              </div>
              {%- if item_meta %}
                <div class="small text-body-secondary mt-1">{{ item_meta }}</div>
              {%- endif %}
              {%- if caller is defined %}
                <div class="mt-2">{{ caller(item) }}</div>
              {%- elif item_body %}
                <p class="small text-body-secondary mb-0 mt-2">{{ item_body }}</p>
              {%- endif %}
            </div>
          </li>
        {%- endfor %}
      </ol>
    </div>
  </section>
{%- endmacro -%}

{%- macro tree_nav_nodes(nodes, tree_id, level=0) -%}
  {%- set nodes = nodes or [] -%}
      <ul class="list-unstyled mb-0
                 {% if level > 0 %}ms-3 mt-2 border-start ps-3{% endif %}">
    {%- for node in nodes %}
      {%- set node_label = (
            node.label if node.label is defined
            else (
              node["label"]
              if node is mapping and "label" in node
              else ""
            )
          ) -%}
      {%- set node_href = (
            node.href if node.href is defined
            else (
              node["href"]
              if node is mapping and "href" in node
              else none
            )
          ) -%}
      {%- set node_icon = (
            node.icon if node.icon is defined
            else (
              node["icon"]
              if node is mapping and "icon" in node
              else none
            )
          ) -%}
      {%- set node_meta = (
            node.meta if node.meta is defined
            else (
              node["meta"]
              if node is mapping and "meta" in node
              else none
            )
          ) -%}
      {%- set node_badge = (
            node.badge if node.badge is defined
            else (
              node["badge"]
              if node is mapping and "badge" in node
              else none
            )
          ) -%}
      {%- set node_active = (
            node.active if node.active is defined
            else (
              node["active"]
              if node is mapping and "active" in node
              else false
            )
          ) -%}
      {%- set node_open = (
            node.open if node.open is defined
            else (
              node["open"]
              if node is mapping and "open" in node
              else false
            )
          ) -%}
      {%- set node_children = (
            node.children if node.children is defined
            else (
              node["children"]
              if node is mapping and "children" in node
              else []
            )
          ) -%}
      <li class="{% if not loop.last %}mb-2{% endif %}">
        {%- if node_children %}
          <details class="jbs-tree-node"{% if node_open %} open{% endif %}>
                <summary class="d-flex flex-wrap align-items-center gap-2
                                rounded-2 px-2 py-1">
              {%- if node_icon %}
                <i class="{{ node_icon }} text-body-secondary" aria-hidden="true"></i>
              {%- endif %}
              <span class="fw-semibold{% if node_active %} text-primary{% endif %}">
                {{ node_label }}
              </span>
              {%- if node_badge %}
                <span class="badge text-bg-light border">{{ node_badge }}</span>
              {%- endif %}
              {%- if node_meta %}
                <span class="small text-body-secondary">{{ node_meta }}</span>
              {%- endif %}
            </summary>
            {{ tree_nav_nodes(node_children, tree_id, level + 1) }}
          </details>
        {%- else %}
              <div class="d-flex flex-wrap align-items-center gap-2
                          rounded-2 px-2 py-1
                          {% if node_active %}bg-primary-subtle{% endif %}">
            {%- if node_icon %}
              <i class="{{ node_icon }} text-body-secondary" aria-hidden="true"></i>
            {%- endif %}
                {%- if node_href %}
                  <a href="{{ node_href }}"
                     class="text-decoration-none{% if node_active %} fw-semibold
                            text-primary{% else %} link-body-emphasis{% endif %}">
                    {{ node_label }}
                  </a>
                {%- else %}
                  <span class="{% if node_active %}fw-semibold text-primary{% endif %}">
                    {{ node_label }}
                  </span>
            {%- endif %}
            {%- if node_badge %}
              <span class="badge text-bg-light border">{{ node_badge }}</span>
            {%- endif %}
            {%- if node_meta %}
              <span class="small text-body-secondary">{{ node_meta }}</span>
            {%- endif %}
          </div>
        {%- endif %}
      </li>
    {%- endfor %}
  </ul>
{%- endmacro -%}

{%- macro tree_nav(tree_id, items, title=None, subtitle=None,
                    class_name="", attrs="") -%}
  {%- set wrapper_classes = "card shadow-sm jbs-tree-nav" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <nav id="{{ tree_id }}"
       class="{{ wrapper_classes }}"
       aria-label="{{ title or 'Tree navigation' }}"
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or subtitle %}
      <div class="card-header bg-body">
        {%- if title %}
          <h2 class="h6 mb-1">{{ title }}</h2>
        {%- endif %}
        {%- if subtitle %}
          <p class="text-body-secondary mb-0">{{ subtitle }}</p>
        {%- endif %}
      </div>
    {%- endif %}
    <div class="card-body">
      {{ tree_nav_nodes(items, tree_id) }}
    </div>
  </nav>
{%- endmacro -%}

{%- macro code_block(block_id=None, code="", language=None, title=None,
                     caption=None, actions_html=None, line_numbers=False,
                     max_height=None, wrap=False, class_name="", attrs="") -%}
  {%- set wrapper_classes = "card shadow-sm jbs-code-block" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  {%- set lines = code.split('\n') -%}
  <section class="{{ wrapper_classes }}"
           {%- if block_id %} id="{{ block_id }}"{% endif -%}
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or language or actions_html %}
          <div class="card-header bg-body d-flex flex-wrap align-items-center
                      justify-content-between gap-2">
        <div class="d-flex flex-wrap align-items-center gap-2">
          {%- if title %}
            <h2 class="h6 mb-0">{{ title }}</h2>
          {%- endif %}
          {%- if language %}
            <span class="badge text-bg-secondary">{{ language }}</span>
          {%- endif %}
        </div>
        {%- if actions_html %}
          <div>{{ actions_html|safe }}</div>
        {%- endif %}
      </div>
    {%- endif %}
    <div class="card-body p-0">
          <div class="overflow-auto bg-dark text-light rounded-bottom"
               {% if max_height %}style="max-height: {{ max_height }};"{% endif %}>
            {%- if line_numbers %}
              <ol class="mb-0 ps-5 pe-3 py-3 font-monospace small"
                  {% if wrap %}style="white-space: pre-wrap;"{% endif %}>
                {%- for line in lines %}
                  <li><code class="text-light">{{ line if line else " " }}</code></li>
                {%- endfor %}
              </ol>
            {%- else %}
              <pre class="mb-0 px-3 py-3 font-monospace small"
                   {% if wrap %}style="white-space: pre-wrap;"{% endif %}><code
                        class="text-light">{{ code }}</code></pre>
            {%- endif %}
      </div>
    </div>
    {%- if caption %}
      <div class="card-footer bg-body small text-body-secondary">{{ caption }}</div>
    {%- endif %}
  </section>
{%- endmacro -%}

{%- macro facet_bar(facet_id, items, title=None, clear_action_html=None,
                    compact=False, class_name="", attrs="") -%}
  {%- set items = items or [] -%}
  {%- set wrapper_classes = "card shadow-sm jbs-facet-bar" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section id="{{ facet_id }}"
           class="{{ wrapper_classes }}"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or clear_action_html %}
      <div class="card-header bg-body d-flex flex-wrap align-items-center
                  justify-content-between gap-2">
        {%- if title %}
          <h2 class="h6 mb-0">{{ title }}</h2>
        {%- endif %}
        {%- if clear_action_html %}
          <div class="ms-auto">{{ clear_action_html|safe }}</div>
        {%- endif %}
      </div>
    {%- endif %}
    <div class="card-body {% if compact %}py-2{% endif %}">
      <div class="d-flex flex-wrap align-items-center gap-2">
        {%- for item in items %}
          {%- set item_label = (
                item.label if item.label is defined
                else (
                  item["label"]
                  if item is mapping and "label" in item
                  else ""
                )
              ) -%}
          {%- set item_value = (
                item.value if item.value is defined
                else (
                  item["value"]
                  if item is mapping and "value" in item
                  else none
                )
              ) -%}
          {%- set item_tone = (
                item.tone if item.tone is defined
                else (
                  item["tone"]
                  if item is mapping and "tone" in item
                  else "light"
                )
              ) -%}
          {%- set item_href = (
                item.href if item.href is defined
                else (
                  item["href"]
                  if item is mapping and "href" in item
                  else none
                )
              ) -%}
          {%- set item_remove_html = (
                item.remove_html if item.remove_html is defined
                else (
                  item["remove_html"]
                  if item is mapping and "remove_html" in item
                  else none
                )
              ) -%}
          <span class="badge rounded-pill text-bg-{{ item_tone }}
                       d-inline-flex align-items-center gap-2 px-3 py-2">
            {%- if item_href %}
              <a href="{{ item_href }}"
                 class="link-body-emphasis text-decoration-none">
                {{ item_label }}
              </a>
            {%- else %}
              <span>{{ item_label }}</span>
            {%- endif %}
            {%- if item_value %}
              <span class="opacity-75">{{ item_value }}</span>
            {%- endif %}
            {%- if item_remove_html %}
              <span class="d-inline-flex align-items-center">
                {{ item_remove_html|safe }}
              </span>
            {%- endif %}
          </span>
        {%- endfor %}
      </div>
    </div>
  </section>
{%- endmacro -%}

{%- macro result_panel(panel_id=None, title=None, subtitle=None,
                       status_badge=None, actions_html=None, body="",
                       empty_html=None, error_html=None, footer=None,
                       class_name="", attrs="") -%}
  {%- set wrapper_classes = "card shadow-sm jbs-result-panel" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section class="{{ wrapper_classes }}"
           {%- if panel_id %} id="{{ panel_id }}"{% endif -%}
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or subtitle or status_badge or actions_html %}
      <div class="card-header bg-body d-flex flex-wrap align-items-start
                  justify-content-between gap-3">
        <div>
          {%- if title %}
            <h2 class="h6 mb-1 d-flex flex-wrap align-items-center gap-2">
              <span>{{ title }}</span>
              {%- if status_badge %}
                {{ status_badge|safe }}
              {%- endif %}
            </h2>
          {%- elif status_badge %}
            <div>{{ status_badge|safe }}</div>
          {%- endif %}
          {%- if subtitle %}
            <p class="text-body-secondary mb-0">{{ subtitle }}</p>
          {%- endif %}
        </div>
        {%- if actions_html %}
          <div class="ms-auto">{{ actions_html|safe }}</div>
        {%- endif %}
      </div>
    {%- endif %}
    <div class="card-body">
      {%- if caller is defined %}
        {{ caller() }}
      {%- elif body %}
        {{ body|safe }}
      {%- elif empty_html %}
        {{ empty_html|safe }}
      {%- endif %}
      {%- if error_html %}
        <div class="{% if body or caller is defined %}mt-3{% endif %}">
          {{ error_html|safe }}
        </div>
      {%- endif %}
    </div>
    {%- if footer %}
      <div class="card-footer bg-body">{{ footer|safe }}</div>
    {%- endif %}
  </section>
{%- endmacro -%}

{%- macro master_detail_shell(shell_id, master_html="", detail_html="",
                              title=None, subtitle=None,
                              header_actions_html=None,
                              master_col_class="col-12 col-lg-4",
                              detail_col_class="col-12 col-lg-8",
                              class_name="", attrs="") -%}
  {%- set wrapper_classes = "card shadow-sm jbs-master-detail-shell" -%}
  {%- if class_name -%}
    {%- set wrapper_classes = wrapper_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <section id="{{ shell_id }}"
           class="{{ wrapper_classes }}"
           {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title or subtitle or header_actions_html %}
      <div class="card-header bg-body d-flex flex-wrap align-items-start
                  justify-content-between gap-3">
        <div>
          {%- if title %}
            <h2 class="h6 mb-1">{{ title }}</h2>
          {%- endif %}
          {%- if subtitle %}
            <p class="text-body-secondary mb-0">{{ subtitle }}</p>
          {%- endif %}
        </div>
        {%- if header_actions_html %}
          <div class="ms-auto">{{ header_actions_html|safe }}</div>
        {%- endif %}
      </div>
    {%- endif %}
    <div class="card-body">
      <div class="row g-3 align-items-stretch">
        <section class="{{ master_col_class }}" data-jbs-pane="master">
          <div class="border rounded-3 h-100 p-3 bg-body-tertiary">
            {{ master_html|safe }}
          </div>
        </section>
        <section class="{{ detail_col_class }}" data-jbs-pane="detail">
          <div class="border rounded-3 h-100 p-3 bg-body">
            {%- if caller is defined %}
              {{ caller() }}
            {%- else %}
              {{ detail_html|safe }}
            {%- endif %}
          </div>
        </section>
      </div>
    </div>
  </section>
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
