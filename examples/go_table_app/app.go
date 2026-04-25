package main

import (
	"cmp"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"slices"
	"strings"
	"sync"
	"time"

	jbs "github.com/abartrim/jinja-bootstrap-spa"
	minijinja "github.com/mitsuhiko/minijinja/minijinja-go/v2"
	"github.com/mitsuhiko/minijinja/minijinja-go/v2/value"
)

const (
	jbsStateHeader       = "X-JBS-State"
	jbsConditionalHeader = "If-None-Match"
	jbsETagHeader        = "ETag"
)

type exampleApp struct {
	env         *minijinja.Environment
	runtimePath string
	state       *appState
}

type appState struct {
	mu sync.Mutex

	orders          []map[string]any
	pushCounter     int
	lastPushMessage string
	ordersStreamSeq int

	livePushCounter int
	liveRows        []map[string]any

	appendPushCounter int
	appendRows        []map[string]any

	orderSubscribers  map[chan map[string]any]struct{}
	liveSubscribers   map[chan map[string]any]struct{}
	appendSubscribers map[chan map[string]any]struct{}
}

type tableStateOptions struct {
	defaultSortBy    string
	defaultPageSize  int
	allowedPageSizes []int
	filterKeys       []string
}

func newExampleApp() (*exampleApp, error) {
	templateDir, runtimePath, err := resolveExamplePaths()
	if err != nil {
		return nil, err
	}

	env, err := jbs.NewEnvironment(jbs.Options{
		TemplateFS: os.DirFS(templateDir),
		URLFor:     jbs.StaticURLFor("/assets"),
	})
	if err != nil {
		return nil, err
	}
	env.SetDebug(true)

	return &exampleApp{
		env:         env,
		runtimePath: runtimePath,
		state: &appState{
			orders: seedOrders(),
			liveRows: []map[string]any{
				{"id": "live-boot", "entry": "boot complete", "source": "runtime"},
				{"id": "live-hydrated", "entry": "table hydrated", "source": "runtime"},
			},
			appendRows: []map[string]any{
				{"id": "append-boot", "entry": "append channel online", "source": "runtime"},
				{"id": "append-ready", "entry": "append stream ready", "source": "runtime"},
			},
			orderSubscribers:  make(map[chan map[string]any]struct{}),
			liveSubscribers:   make(map[chan map[string]any]struct{}),
			appendSubscribers: make(map[chan map[string]any]struct{}),
		},
	}, nil
}

func resolveExamplePaths() (templateDir string, runtimePath string, err error) {
	_, thisFile, _, ok := runtime.Caller(0)
	if !ok {
		return "", "", errors.New("resolve example paths: runtime caller unavailable")
	}

	exampleDir := filepath.Dir(thisFile)
	templateDir = filepath.Join(exampleDir, "../table_app/templates")
	runtimePath = filepath.Join(
		exampleDir,
		"../../src/jinja_bootstrap_spa/static/jinja-bootstrap-spa.js",
	)
	return filepath.Clean(templateDir), filepath.Clean(runtimePath), nil
}

func (app *exampleApp) routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /", app.handleIndex)
	mux.HandleFunc("GET /components/orders", app.handleOrdersComponent)
	mux.HandleFunc("GET /components/live-table", app.handleLiveTableComponent)
	mux.HandleFunc("GET /components/live-append-table", app.handleLiveAppendTableComponent)
	mux.HandleFunc("GET /components/session-table", app.handleSessionTableComponent)
	mux.HandleFunc("GET /components/foundation-grid", app.handleFoundationGridComponent)
	mux.HandleFunc("GET /components/foundation-work-queue", app.handleFoundationWorkQueueComponent)
	mux.HandleFunc("GET /components/cancel-demo", app.handleCancelDemoComponent)
	mux.HandleFunc("GET /components/lazy-summary", app.handleLazySummaryComponent)
	mux.HandleFunc("GET /fragments/customer-options", app.handleCustomerOptions)
	mux.HandleFunc("GET /assets/jinja-bootstrap-spa.js", app.handleRuntimeJS)
	mux.HandleFunc("GET /events/orders", app.handleOrdersEvents)
	mux.HandleFunc("GET /events/live-table", app.handleLiveTableEvents)
	mux.HandleFunc("GET /events/live-append-table", app.handleLiveAppendTableEvents)
	mux.HandleFunc("POST /admin/simulate-update", app.handleSimulateUpdate)
	mux.HandleFunc("POST /admin/push-live-row", app.handlePushLiveRow)
	mux.HandleFunc("POST /admin/push-live-append-row", app.handlePushLiveAppendRow)
	mux.HandleFunc("GET /api/sql-hints", app.handleSQLHints)
	mux.HandleFunc("POST /api/sql-validate", app.handleSQLValidate)
	mux.HandleFunc("POST /api/validate-regex", app.handleValidateRegex)
	return mux
}

func (app *exampleApp) handleIndex(w http.ResponseWriter, r *http.Request) {
	context, err := app.buildIndexContext(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	app.renderPage(w, "index.html", context)
}

func (app *exampleApp) handleOrdersComponent(w http.ResponseWriter, r *http.Request) {
	context, err := app.buildOrdersContext(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	html, err := app.renderTemplate("partials/orders_table.html", context)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeConditionalFragment(w, r, html)
}

func (app *exampleApp) handleLiveTableComponent(w http.ResponseWriter, r *http.Request) {
	context := app.buildLiveTableContext(r)
	app.renderFragment(w, r, "partials/live_table.html", context)
}

func (app *exampleApp) handleLiveAppendTableComponent(w http.ResponseWriter, r *http.Request) {
	context := app.buildLiveAppendContext(r)
	app.renderFragment(w, r, "partials/live_append_table.html", context)
}

func (app *exampleApp) handleSessionTableComponent(w http.ResponseWriter, r *http.Request) {
	context, err := app.buildOrdersContext(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	for key, value := range app.buildSessionContext(r) {
		context[key] = value
	}
	app.renderFragment(w, r, "partials/session_table.html", context)
}

func (app *exampleApp) handleFoundationGridComponent(w http.ResponseWriter, r *http.Request) {
	app.renderFragment(w, r, "partials/foundation_grid.html", app.buildFoundationGridContext())
}

func (app *exampleApp) handleFoundationWorkQueueComponent(w http.ResponseWriter, r *http.Request) {
	app.renderFragment(w, r, "partials/foundation_work_queue.html", app.buildFoundationWorkQueueContext(r))
}

func (app *exampleApp) handleCancelDemoComponent(w http.ResponseWriter, r *http.Request) {
	value := cmp.Or(r.URL.Query().Get("value"), "idle")
	delayMS := clamp(parsePositiveInt(r.URL.Query().Get("delay_ms"), 0), 0, 1000)
	if delayMS > 0 {
		time.Sleep(time.Duration(delayMS) * time.Millisecond)
	}
	app.renderFragment(w, r, "partials/cancel_demo.html", map[string]any{
		"value":    value,
		"delay_ms": delayMS,
	})
}

func (app *exampleApp) handleLazySummaryComponent(w http.ResponseWriter, r *http.Request) {
	html := `<section id="lazy-summary" class="card p-3 border-success-subtle" data-jbs-component="lazy-summary" data-jbs-endpoint="/components/lazy-summary" data-jbs-target="#lazy-summary" data-jbs-key="lazy-summary" data-jbs-persist="memory" data-jbs-stream-mode="replace" data-jbs-stream-pause-when-hidden="false" data-jbs-stream-buffer-max="50" data-jbs-state='{}'><strong class="text-success">Lazy summary ready.</strong> <span class="text-body-secondary">Loaded on first viewport entry.</span></section>`
	writeConditionalFragment(w, r, html)
}

func (app *exampleApp) handleCustomerOptions(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	app.renderFragment(w, r, "partials/customer_autocomplete_options.html", map[string]any{
		"matches": app.customerMatches(query),
	})
}

func (app *exampleApp) handleRuntimeJS(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, app.runtimePath)
}

func (app *exampleApp) handleOrdersEvents(w http.ResponseWriter, r *http.Request) {
	app.serveSSE(
		w,
		r,
		func(ch chan map[string]any) { app.addSubscriber(&app.state.orderSubscribers, ch) },
		func(ch chan map[string]any) { app.removeSubscriber(&app.state.orderSubscribers, ch) },
	)
}

func (app *exampleApp) handleLiveTableEvents(w http.ResponseWriter, r *http.Request) {
	app.serveSSE(
		w,
		r,
		func(ch chan map[string]any) { app.addSubscriber(&app.state.liveSubscribers, ch) },
		func(ch chan map[string]any) { app.removeSubscriber(&app.state.liveSubscribers, ch) },
	)
}

func (app *exampleApp) handleLiveAppendTableEvents(w http.ResponseWriter, r *http.Request) {
	app.serveSSE(
		w,
		r,
		func(ch chan map[string]any) { app.addSubscriber(&app.state.appendSubscribers, ch) },
		func(ch chan map[string]any) { app.removeSubscriber(&app.state.appendSubscribers, ch) },
	)
}

func (app *exampleApp) handleSimulateUpdate(w http.ResponseWriter, r *http.Request) {
	app.state.mu.Lock()
	defer app.state.mu.Unlock()

	app.state.pushCounter++
	order := app.state.orders[app.state.pushCounter%len(app.state.orders)]
	if order["status"] != "open" {
		order["status"] = "open"
	} else {
		order["status"] = "queued"
	}

	app.state.lastPushMessage = fmt.Sprintf(
		"SSE update #%d: %s is now %s.",
		app.state.pushCounter,
		order["number"],
		order["status"],
	)
	message := app.state.lastPushMessage
	app.publishOrdersEventLocked(message, nil)
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "message": message})
}

func (app *exampleApp) handlePushLiveRow(w http.ResponseWriter, r *http.Request) {
	app.state.mu.Lock()
	defer app.state.mu.Unlock()

	app.state.livePushCounter++
	row := map[string]any{
		"id":     fmt.Sprintf("live-%d", app.state.livePushCounter),
		"entry":  fmt.Sprintf("event-%d", app.state.livePushCounter),
		"source": "sse",
	}
	app.state.liveRows = append([]map[string]any{row}, app.state.liveRows...)

	app.publishLocked(
		app.state.liveSubscribers,
		map[string]any{
			"v":      1,
			"seq":    app.state.livePushCounter,
			"target": "live-table",
			"ops": []map[string]any{
				{
					"op":       "upsert",
					"id":       row["id"],
					"position": "prepend",
					"html":     renderLiveRow(row["id"], row["entry"], row["source"]),
				},
			},
		},
	)
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "entry": row["entry"]})
}

func (app *exampleApp) handlePushLiveAppendRow(w http.ResponseWriter, r *http.Request) {
	app.state.mu.Lock()
	defer app.state.mu.Unlock()

	app.state.appendPushCounter++
	row := map[string]any{
		"id":     fmt.Sprintf("append-%d", app.state.appendPushCounter),
		"entry":  fmt.Sprintf("append-%d", app.state.appendPushCounter),
		"source": "sse",
	}
	app.state.appendRows = append(app.state.appendRows, row)
	pageSize := 5
	pageCount := maxInt(1, (len(app.state.appendRows)+pageSize-1)/pageSize)

	app.publishLocked(
		app.state.appendSubscribers,
		map[string]any{
			"v":      1,
			"seq":    app.state.appendPushCounter,
			"target": "live-append-table",
			"ops": []map[string]any{
				{
					"op":       "upsert",
					"id":       row["id"],
					"position": "append",
					"html":     renderLiveRow(row["id"], row["entry"], row["source"]),
				},
			},
			"meta": map[string]any{
				"total_rows":   len(app.state.appendRows),
				"page_count":   pageCount,
				"showing_rows": minInt(pageSize, len(app.state.appendRows)),
				"subtitle":     "SSE stream appends rows while table metadata stays in sync.",
			},
		},
	)
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "entry": row["entry"]})
}

func (app *exampleApp) handleSQLHints(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"hints": []string{"service", "status", "duration_ms", "AND", "OR", "ILIKE"},
	})
}

func (app *exampleApp) handleSQLValidate(w http.ResponseWriter, r *http.Request) {
	var payload map[string]any
	_ = json.NewDecoder(r.Body).Decode(&payload)
	sqlText := strings.TrimSpace(stringValue(payload["sql"]))
	switch {
	case sqlText == "":
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "message": "SQL filter is empty."})
	case strings.Contains(strings.ToLower(sqlText), "drop "):
		writeJSON(w, http.StatusOK, map[string]any{
			"ok": false,
			"issues": []map[string]any{
				{"level": "error", "message": "Forbidden keyword."},
			},
		})
	case strings.HasSuffix(sqlText, "AND"), strings.HasSuffix(sqlText, "OR"):
		writeJSON(w, http.StatusOK, map[string]any{
			"ok": false,
			"issues": []map[string]any{
				{"level": "warning", "message": "Expression ends with an operator."},
			},
		})
	default:
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "message": "SQL filter validated."})
	}
}

func (app *exampleApp) handleValidateRegex(w http.ResponseWriter, r *http.Request) {
	var payload map[string]any
	_ = json.NewDecoder(r.Body).Decode(&payload)
	regexValue := strings.TrimSpace(stringValue(payload["query"]))
	if regexValue == "" {
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "message": "Regex filter is empty."})
		return
	}

	if _, err := regexp.Compile(regexValue); err != nil {
		writeJSON(w, http.StatusOK, map[string]any{
			"ok": false,
			"issues": []map[string]any{
				{"level": "error", "message": fmt.Sprintf("Invalid regex: %v", err)},
			},
		})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "message": "Regex filter validated."})
}

func (app *exampleApp) buildIndexContext(r *http.Request) (map[string]any, error) {
	context, err := app.buildOrdersContext(r)
	if err != nil {
		return nil, err
	}
	for key, value := range app.buildSessionContext(r) {
		context[key] = value
	}
	for key, value := range app.buildFoundationWorkQueueContext(r) {
		context[key] = value
	}
	for key, value := range app.buildLiveTableContext(r) {
		context[key] = value
	}
	for key, value := range app.buildLiveAppendContext(r) {
		context[key] = value
	}
	for key, value := range app.buildFoundationGridContext() {
		context[key] = value
	}
	return context, nil
}

func (app *exampleApp) buildOrdersContext(r *http.Request) (map[string]any, error) {
	state := parseTableState(r, tableStateOptions{
		defaultSortBy:    "number",
		defaultPageSize:  8,
		allowedPageSizes: []int{4, 8, 12, 20},
		filterKeys:       []string{"status", "customer", "row_id", "intent", "from_ts", "to_ts", "sql", "regex"},
	})

	actionMessage := ""

	app.state.mu.Lock()
	defer app.state.mu.Unlock()

	rowID := cmp.Or(stringValue(state["row_id"]), "")
	intent := cmp.Or(stringValue(state["intent"]), "")
	if rowID != "" && intent != "" {
		actionMessage = app.applyRowActionLocked(rowID, intent)
		delete(state, "row_id")
		delete(state, "intent")
	}

	filteredRows := filterOrders(
		app.state.orders,
		stringValue(state["query"]),
		stringValue(state["status"]),
		stringValue(state["customer"]),
		stringValue(state["regex"]),
	)
	sortedRows := sortOrders(
		filteredRows,
		cmp.Or(stringValue(state["sort_by"]), "number"),
		cmp.Or(stringValue(state["sort_dir"]), "asc"),
	)

	page := intValue(state["page"], 1)
	pageSize := intValue(state["page_size"], 8)
	start := maxInt(0, (page-1)*pageSize)
	end := minInt(len(sortedRows), start+pageSize)
	pageRows := sortedRows
	if start < len(sortedRows) {
		pageRows = sortedRows[start:end]
	} else {
		pageRows = []map[string]any{}
	}

	rows := make([]map[string]any, 0, len(pageRows))
	for _, order := range pageRows {
		menu, err := app.renderTemplate("partials/order_action_menu.html", map[string]any{
			"menu_id": fmt.Sprintf("%s-actions", order["id"]),
			"order":   order,
			"items": []map[string]any{
				{"label": "Inspect Order", "href": fmt.Sprintf("/?query=%v", order["number"])},
				{"divider": true},
				{
					"label":             ternary(order["status"] == "archived", "Restore Order", "Archive Order"),
					"jbs_action":        "row",
					"jbs_row_id":        order["id"],
					"jbs_intent":        ternary(order["status"] == "archived", "restore", "archive"),
					"variant":           "danger",
					"jbs_component_ref": "",
				},
			},
		})
		if err != nil {
			return nil, err
		}

		rows = append(rows, map[string]any{
			"id":       order["id"],
			"number":   order["number"],
			"customer": order["customer"],
			"status":   strings.Title(stringValue(order["status"])),
			"total":    fmt.Sprintf("$%.2f", floatValue(order["total"])),
			"actions":  menu,
		})
	}

	subtitle := "Exercise sort, paging, filters, row actions, and SSE-driven refreshes."
	var statusNotice map[string]any
	if app.state.lastPushMessage != "" {
		subtitle = app.state.lastPushMessage
		statusNotice = map[string]any{
			"title":   "Live Update",
			"message": app.state.lastPushMessage,
			"variant": "info",
		}
	}
	if actionMessage != "" {
		subtitle = actionMessage
		statusNotice = map[string]any{
			"title":   "Row Action",
			"message": actionMessage,
			"variant": "success",
		}
	}

	return map[string]any{
		"rows":            rows,
		"total_rows":      len(sortedRows),
		"table_state":     state,
		"subtitle":        subtitle,
		"runtime_url":     value.FromSafeString("/assets/jinja-bootstrap-spa.js"),
		"push_url":        value.FromSafeString("/admin/simulate-update"),
		"live_push_url":   value.FromSafeString("/admin/push-live-row"),
		"append_push_url": value.FromSafeString("/admin/push-live-append-row"),
		"live_rows":       cloneRows(app.state.liveRows),
		"append_rows":     cloneRows(app.state.appendRows),
		"status_summary":  statusSummary(filteredRows),
		"status_notice":   statusNotice,
	}, nil
}

func (app *exampleApp) buildSessionContext(r *http.Request) map[string]any {
	state := parseTableState(r, tableStateOptions{
		defaultSortBy:    "name",
		defaultPageSize:  2,
		allowedPageSizes: []int{2, 4},
	})
	rowsSorted := slices.Clone(sessionRows)
	slices.SortFunc(rowsSorted, func(a, b map[string]any) int {
		return strings.Compare(stringValue(a["name"]), stringValue(b["name"]))
	})
	page := intValue(state["page"], 1)
	pageSize := intValue(state["page_size"], 2)
	start := maxInt(0, (page-1)*pageSize)
	end := minInt(len(rowsSorted), start+pageSize)
	selected := []map[string]any{}
	if start < len(rowsSorted) {
		selected = rowsSorted[start:end]
	}
	return map[string]any{
		"session_rows":       selected,
		"session_total_rows": len(rowsSorted),
		"session_state":      state,
	}
}

func (app *exampleApp) buildFoundationWorkQueueContext(r *http.Request) map[string]any {
	state := parseTableState(r, tableStateOptions{
		defaultSortBy:    "service",
		defaultPageSize:  3,
		allowedPageSizes: []int{3, 6},
		filterKeys:       []string{"selected_ids"},
	})

	selectedIDs := []string{}
	switch value := state["selected_ids"].(type) {
	case []string:
		selectedIDs = value
	case string:
		selectedIDs = []string{value}
	}

	sortBy := cmp.Or(stringValue(state["sort_by"]), "service")
	sortDir := cmp.Or(stringValue(state["sort_dir"]), "asc")
	reverse := sortDir == "desc"

	rowsSorted := slices.Clone(foundationWorkQueue)
	slices.SortFunc(rowsSorted, func(a, b map[string]any) int {
		left := strings.ToLower(stringValue(a[sortBy]))
		right := strings.ToLower(stringValue(b[sortBy]))
		if reverse {
			return strings.Compare(right, left)
		}
		return strings.Compare(left, right)
	})

	page := intValue(state["page"], 1)
	pageSize := intValue(state["page_size"], 3)
	start := maxInt(0, (page-1)*pageSize)
	end := minInt(len(rowsSorted), start+pageSize)
	pageRows := []map[string]any{}
	if start < len(rowsSorted) {
		pageRows = rowsSorted[start:end]
	}

	selectedLabel := "Selectable rows keep state through page and sort actions."
	if len(selectedIDs) > 0 {
		selectedLabel = fmt.Sprintf("%d selected across refreshes and page changes.", len(selectedIDs))
	}

	return map[string]any{
		"foundation_work_queue_rows":         pageRows,
		"foundation_work_queue_total_rows":   len(rowsSorted),
		"foundation_work_queue_state":        state,
		"foundation_work_queue_selected_ids": selectedIDs,
		"foundation_work_queue_subtitle": "Pinned start/end columns plus header-based selection state. " +
			selectedLabel,
	}
}

func (app *exampleApp) buildLiveTableContext(r *http.Request) map[string]any {
	state := parseTableState(r, tableStateOptions{
		defaultPageSize:  5,
		allowedPageSizes: []int{5},
	})

	app.state.mu.Lock()
	defer app.state.mu.Unlock()
	page := intValue(state["page"], 1)
	pageSize := intValue(state["page_size"], 5)
	start := maxInt(0, (page-1)*pageSize)
	end := minInt(len(app.state.liveRows), start+pageSize)
	rows := []map[string]any{}
	if start < len(app.state.liveRows) {
		rows = cloneRows(app.state.liveRows[start:end])
	}
	return map[string]any{
		"live_rows":       rows,
		"live_total_rows": len(app.state.liveRows),
		"live_state":      state,
	}
}

func (app *exampleApp) buildLiveAppendContext(r *http.Request) map[string]any {
	state := parseTableState(r, tableStateOptions{
		defaultPageSize:  5,
		allowedPageSizes: []int{5},
	})

	app.state.mu.Lock()
	defer app.state.mu.Unlock()
	page := intValue(state["page"], 1)
	pageSize := intValue(state["page_size"], 5)
	start := maxInt(0, (page-1)*pageSize)
	end := minInt(len(app.state.appendRows), start+pageSize)
	rows := []map[string]any{}
	if start < len(app.state.appendRows) {
		rows = cloneRows(app.state.appendRows[start:end])
	}
	return map[string]any{
		"append_rows":       rows,
		"append_total_rows": len(app.state.appendRows),
		"append_state":      state,
	}
}

func (app *exampleApp) buildFoundationGridContext() map[string]any {
	return map[string]any{
		"foundation_grid_rows": []map[string]any{
			{"primitive": "data_grid", "purpose": "Reusable CRUD and operator shell for table-driven pages.", "status": `<span class="badge text-bg-success">Implemented</span>`},
			{"primitive": "searchable_expandable_list", "purpose": "Explorer shell for drill-down lists and schema browsers.", "status": `<span class="badge text-bg-success">Implemented</span>`},
			{"primitive": "workspace_modal", "purpose": "Large overlay for editors, inspectors, and multi-pane flows.", "status": `<span class="badge text-bg-primary">Ready to compose</span>`},
			{"primitive": "timeline", "purpose": "Ordered event/history surface for audit trails and stream summaries.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "stacked_list", "purpose": "Compact stacked rows for queues, review surfaces, and result summaries.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "tree_nav", "purpose": "Hierarchical explorer navigation without a separate JS tree widget.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "code_block", "purpose": "Structured snippet/config surface for docs, query output, and operator hints.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "facet_bar", "purpose": "Active-filter chip row with clear/remove affordances for tables and explorers.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "master_detail_shell", "purpose": "Generic master/detail layout for inspector, review, and explorer pages.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "result_panel", "purpose": "Consistent output surface for generated results, previews, and validation summaries.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "command_bar", "purpose": "Reusable action strip for search, quick actions, and overflow commands.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "metric_grid", "purpose": "Structured summary band for grouped stat cards and KPI rows.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "activity_feed", "purpose": "Dense event stream surface for audits, comments, and runtime activity.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "property_editor", "purpose": "Inspector-style form shell for settings, metadata, and builder properties.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "diff_view", "purpose": "Before/after comparison shell for config reviews and change inspection.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "filterable_card_list", "purpose": "Filterable card-grid shell for dashboards, explorers, and work queues.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "inline_edit_shell", "purpose": "Detail-and-editor shell for inline review and editing workflows.", "status": `<span class="badge text-bg-success">New</span>`},
			{"primitive": "table selection + pinned columns", "purpose": "Generic dense-grid enhancements for bulk actions and operator views.", "status": `<span class="badge text-bg-success">New</span>`},
		},
		"foundation_grid_state": map[string]any{
			"page":      1,
			"page_size": 10,
			"sort_by":   "",
			"sort_dir":  "asc",
		},
	}
}

func (app *exampleApp) renderPage(w http.ResponseWriter, templateName string, context map[string]any) {
	rendered, err := app.renderTemplate(templateName, context)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	_, _ = io.WriteString(w, rendered)
}

func (app *exampleApp) renderFragment(w http.ResponseWriter, r *http.Request, templateName string, context map[string]any) {
	rendered, err := app.renderTemplate(templateName, context)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeConditionalFragment(w, r, rendered)
}

func (app *exampleApp) renderTemplate(templateName string, context map[string]any) (string, error) {
	tmpl, err := app.env.GetTemplate(templateName)
	if err != nil {
		return "", fmt.Errorf("get template %s: %#v", templateName, err)
	}
	rendered, err := tmpl.Render(context)
	if err != nil {
		return "", fmt.Errorf("render template %s: %#v", templateName, err)
	}
	return rendered, nil
}

func writeConditionalFragment(w http.ResponseWriter, r *http.Request, content string) {
	etag := fragmentETag(content)
	w.Header().Set(jbsETagHeader, etag)
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if etagMatches(r.Header.Get(jbsConditionalHeader), etag) {
		w.WriteHeader(http.StatusNotModified)
		return
	}
	_, _ = io.WriteString(w, content)
}

func fragmentETag(content string) string {
	digest := sha256.Sum256([]byte(content))
	return `W/"jbs-` + hex.EncodeToString(digest[:])[:24] + `"`
}

func etagMatches(header string, etag string) bool {
	if strings.TrimSpace(header) == "" {
		return false
	}

	candidates := strings.Split(header, ",")
	strongETag := strings.TrimPrefix(etag, "W/")
	weakETag := "W/" + strongETag
	for _, candidate := range candidates {
		token := strings.TrimSpace(candidate)
		if token == "" {
			continue
		}
		candidateStrong := strings.TrimPrefix(token, "W/")
		if token == "*" || token == etag || token == strongETag || token == weakETag {
			return true
		}
		if candidateStrong == strongETag {
			return true
		}
	}
	return false
}

func parseTableState(r *http.Request, opts tableStateOptions) map[string]any {
	headerState := map[string]any{}
	if raw := r.Header.Get(jbsStateHeader); raw != "" {
		_ = json.Unmarshal([]byte(raw), &headerState)
	}

	getStateValue := func(key string, fallback any) any {
		if value, ok := headerState[key]; ok {
			return value
		}
		values := r.URL.Query()[key]
		if len(values) == 0 {
			return fallback
		}
		if len(values) == 1 {
			return values[0]
		}
		result := make([]string, 0, len(values))
		for _, value := range values {
			if value != "" {
				result = append(result, value)
			}
		}
		return result
	}

	allowedSizes := make(map[int]struct{}, len(opts.allowedPageSizes))
	for _, size := range opts.allowedPageSizes {
		allowedSizes[size] = struct{}{}
	}

	page := parsePositiveInt(getStateValue("page", 1), 1)
	pageSize := parsePositiveInt(getStateValue("page_size", opts.defaultPageSize), opts.defaultPageSize)
	if len(allowedSizes) > 0 {
		if _, ok := allowedSizes[pageSize]; !ok {
			pageSize = opts.defaultPageSize
		}
	}

	sortBy := cmp.Or(stringValue(getStateValue("sort_by", opts.defaultSortBy)), opts.defaultSortBy)
	sortDir := cmp.Or(stringValue(getStateValue("sort_dir", "asc")), "asc")
	if sortDir != "asc" && sortDir != "desc" {
		sortDir = "asc"
	}

	state := map[string]any{
		"page":      page,
		"page_size": pageSize,
		"sort_by":   sortBy,
		"sort_dir":  sortDir,
	}

	if query := strings.TrimSpace(stringValue(getStateValue("query", ""))); query != "" {
		state["query"] = query
	}

	for _, key := range opts.filterKeys {
		value := getStateValue(key, nil)
		switch typed := value.(type) {
		case []string:
			filtered := make([]string, 0, len(typed))
			for _, item := range typed {
				if item != "" {
					filtered = append(filtered, item)
				}
			}
			if len(filtered) > 0 {
				state[key] = filtered
			}
		case []any:
			filtered := make([]string, 0, len(typed))
			for _, item := range typed {
				rendered := strings.TrimSpace(stringValue(item))
				if rendered != "" {
					filtered = append(filtered, rendered)
				}
			}
			if len(filtered) > 0 {
				state[key] = filtered
			}
		default:
			if rendered := strings.TrimSpace(stringValue(typed)); rendered != "" {
				state[key] = rendered
			}
		}
	}

	return state
}

func filterOrders(rows []map[string]any, query string, status string, customer string, regexFilter string) []map[string]any {
	filtered := cloneRows(rows)
	if query != "" {
		queryLower := strings.ToLower(query)
		next := make([]map[string]any, 0, len(filtered))
		for _, row := range filtered {
			if strings.Contains(strings.ToLower(stringValue(row["number"])), queryLower) ||
				strings.Contains(strings.ToLower(stringValue(row["customer"])), queryLower) {
				next = append(next, row)
			}
		}
		filtered = next
	}
	if status != "" {
		next := make([]map[string]any, 0, len(filtered))
		for _, row := range filtered {
			if stringValue(row["status"]) == status {
				next = append(next, row)
			}
		}
		filtered = next
	}
	if customer != "" {
		next := make([]map[string]any, 0, len(filtered))
		for _, row := range filtered {
			if strings.EqualFold(stringValue(row["customer"]), customer) {
				next = append(next, row)
			}
		}
		filtered = next
	}
	if regexFilter != "" {
		pattern, err := regexp.Compile("(?i)" + regexFilter)
		if err != nil {
			return filtered
		}
		next := make([]map[string]any, 0, len(filtered))
		for _, row := range filtered {
			if pattern.MatchString(stringValue(row["number"])) || pattern.MatchString(stringValue(row["customer"])) {
				next = append(next, row)
			}
		}
		filtered = next
	}
	return filtered
}

func sortOrders(rows []map[string]any, sortBy string, sortDir string) []map[string]any {
	if !slices.Contains([]string{"number", "customer", "status", "total"}, sortBy) {
		sortBy = "number"
	}
	reverse := sortDir == "desc"
	sorted := cloneRows(rows)
	slices.SortFunc(sorted, func(a, b map[string]any) int {
		var compare int
		if sortBy == "total" {
			left := floatValue(a["total"])
			right := floatValue(b["total"])
			compare = cmp.Compare(left, right)
		} else {
			compare = strings.Compare(stringValue(a[sortBy]), stringValue(b[sortBy]))
		}
		if reverse {
			return -compare
		}
		return compare
	})
	return sorted
}

func statusSummary(rows []map[string]any) []map[string]any {
	counts := map[string]int{"Queued": 0, "Open": 0, "Archived": 0}
	for _, row := range rows {
		switch stringValue(row["status"]) {
		case "queued":
			counts["Queued"]++
		case "open":
			counts["Open"]++
		case "archived":
			counts["Archived"]++
		}
	}
	return []map[string]any{
		{"label": "Queued", "count": counts["Queued"]},
		{"label": "Open", "count": counts["Open"]},
		{"label": "Archived", "count": counts["Archived"]},
	}
}

func (app *exampleApp) customerMatches(query string) []string {
	app.state.mu.Lock()
	defer app.state.mu.Unlock()

	unique := make(map[string]struct{})
	for _, order := range app.state.orders {
		unique[stringValue(order["customer"])] = struct{}{}
	}
	customers := make([]string, 0, len(unique))
	for customer := range unique {
		customers = append(customers, customer)
	}
	slices.Sort(customers)

	queryLower := strings.ToLower(strings.TrimSpace(query))
	if queryLower == "" {
		return take(customers, 8)
	}
	matches := make([]string, 0, len(customers))
	for _, customer := range customers {
		if strings.Contains(strings.ToLower(customer), queryLower) {
			matches = append(matches, customer)
		}
	}
	return take(matches, 8)
}

func (app *exampleApp) applyRowActionLocked(rowID string, intent string) string {
	for _, order := range app.state.orders {
		if stringValue(order["id"]) != rowID {
			continue
		}
		switch intent {
		case "archive":
			order["status"] = "archived"
		case "restore":
			order["status"] = "queued"
		default:
			return ""
		}
		message := fmt.Sprintf("%sd %s", strings.Title(intent), order["number"])
		app.publishOrdersEventLocked(message, nil)
		return message
	}
	return ""
}

func renderLiveRow(rowID any, entry any, source any) string {
	return fmt.Sprintf(
		`<tr data-jbs-row-id="%s"><td>%s</td><td>%s</td></tr>`,
		html.EscapeString(stringValue(rowID)),
		html.EscapeString(stringValue(entry)),
		html.EscapeString(stringValue(source)),
	)
}

func (app *exampleApp) addSubscriber(registry *map[chan map[string]any]struct{}, ch chan map[string]any) {
	app.state.mu.Lock()
	defer app.state.mu.Unlock()
	(*registry)[ch] = struct{}{}
}

func (app *exampleApp) removeSubscriber(registry *map[chan map[string]any]struct{}, ch chan map[string]any) {
	app.state.mu.Lock()
	defer app.state.mu.Unlock()
	delete(*registry, ch)
	close(ch)
}

func (app *exampleApp) serveSSE(
	w http.ResponseWriter,
	r *http.Request,
	register func(chan map[string]any),
	unregister func(chan map[string]any),
) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}

	ch := make(chan map[string]any, 8)
	register(ch)
	defer unregister(ch)

	headers := w.Header()
	headers.Set("Content-Type", "text/event-stream")
	headers.Set("Cache-Control", "no-cache")
	headers.Set("Connection", "keep-alive")
	headers.Set("X-Accel-Buffering", "no")
	_, _ = io.WriteString(w, "retry: 3000\n\n")
	flusher.Flush()

	keepAlive := time.NewTicker(15 * time.Second)
	defer keepAlive.Stop()

	for {
		select {
		case <-r.Context().Done():
			return
		case payload := <-ch:
			data, err := json.Marshal(payload)
			if err != nil {
				log.Printf("marshal sse payload: %v", err)
				continue
			}
			_, _ = fmt.Fprintf(w, "event: refresh\ndata: %s\n\n", data)
			flusher.Flush()
		case <-keepAlive.C:
			_, _ = io.WriteString(w, ": keep-alive\n\n")
			flusher.Flush()
		}
	}
}

func (app *exampleApp) publishOrdersEventLocked(message string, patch map[string]any) {
	app.state.ordersStreamSeq++
	if patch == nil {
		patch = map[string]any{}
	}
	payload := map[string]any{
		"v":        1,
		"seq":      app.state.ordersStreamSeq,
		"action":   "refresh",
		"target":   "orders-table",
		"patch":    patch,
		"snapshot": fmt.Sprintf("orders-%d", app.state.ordersStreamSeq),
	}
	app.publishLocked(app.state.orderSubscribers, payload)
}

func (app *exampleApp) publishLocked(registry map[chan map[string]any]struct{}, payload map[string]any) {
	for subscriber := range registry {
		select {
		case subscriber <- payload:
		default:
		}
	}
}

func writeJSON(w http.ResponseWriter, status int, payload map[string]any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func parsePositiveInt(raw any, fallback int) int {
	switch value := raw.(type) {
	case int:
		if value >= 1 {
			return value
		}
	case int64:
		if value >= 1 {
			return int(value)
		}
	case float64:
		if value >= 1 {
			return int(value)
		}
	case json.Number:
		if parsed, err := value.Int64(); err == nil && parsed >= 1 {
			return int(parsed)
		}
	case string:
		if parsed, err := fmt.Sscanf(strings.TrimSpace(value), "%d", &fallback); err == nil && parsed == 1 && fallback >= 1 {
			return fallback
		}
	}
	return fallback
}

func intValue(raw any, fallback int) int {
	return parsePositiveInt(raw, fallback)
}

func floatValue(raw any) float64 {
	switch value := raw.(type) {
	case float64:
		return value
	case float32:
		return float64(value)
	case int:
		return float64(value)
	case int64:
		return float64(value)
	case json.Number:
		parsed, _ := value.Float64()
		return parsed
	case string:
		var parsed float64
		_, _ = fmt.Sscanf(value, "%f", &parsed)
		return parsed
	default:
		return 0
	}
}

func stringValue(raw any) string {
	switch value := raw.(type) {
	case nil:
		return ""
	case string:
		return value
	case json.Number:
		return value.String()
	default:
		return fmt.Sprint(value)
	}
}

func cloneRows(rows []map[string]any) []map[string]any {
	cloned := make([]map[string]any, 0, len(rows))
	for _, row := range rows {
		next := make(map[string]any, len(row))
		for key, value := range row {
			next[key] = value
		}
		cloned = append(cloned, next)
	}
	return cloned
}

func take(values []string, limit int) []string {
	if len(values) <= limit {
		return values
	}
	return values[:limit]
}

func clamp(value int, minimum int, maximum int) int {
	return minInt(maxInt(value, minimum), maximum)
}

func minInt(left int, right int) int {
	if left < right {
		return left
	}
	return right
}

func maxInt(left int, right int) int {
	if left > right {
		return left
	}
	return right
}

func ternary(condition bool, whenTrue string, whenFalse string) string {
	if condition {
		return whenTrue
	}
	return whenFalse
}
