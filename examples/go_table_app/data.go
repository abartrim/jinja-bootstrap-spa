package main

import "fmt"

var sessionRows = []map[string]any{
	{"name": "Alerts", "owner": "SRE"},
	{"name": "Incidents", "owner": "On-call"},
	{"name": "Traces", "owner": "Platform"},
	{"name": "Errors", "owner": "Backend"},
	{"name": "Web Traffic", "owner": "Growth"},
	{"name": "AI Calls", "owner": "Infra"},
}

var foundationWorkQueue = []map[string]any{
	{
		"id":       "queue-101",
		"service":  "orders-api",
		"owner":    "Platform",
		"priority": "P1",
		"status":   "Queued",
		"window":   "2026-04-19 08:00",
		"summary":  "Roll out fragment cache headers and state-aware refresh handling.",
	},
	{
		"id":       "queue-102",
		"service":  "reporting-ui",
		"owner":    "Analytics",
		"priority": "P2",
		"status":   "Review",
		"window":   "2026-04-19 09:15",
		"summary":  "Backfill generic chart shell usage before dashboard migration.",
	},
	{
		"id":       "queue-103",
		"service":  "audit-stream",
		"owner":    "Operations",
		"priority": "P1",
		"status":   "Ready",
		"window":   "2026-04-19 10:00",
		"summary":  "Promote SSE delta protocol and verify hidden-tab buffering behavior.",
	},
	{
		"id":       "queue-104",
		"service":  "table-explorer",
		"owner":    "Data",
		"priority": "P3",
		"status":   "Queued",
		"window":   "2026-04-19 11:30",
		"summary":  "Adopt tree navigation, inline review panes, and card collections.",
	},
	{
		"id":       "queue-105",
		"service":  "operator-console",
		"owner":    "SRE",
		"priority": "P2",
		"status":   "Review",
		"window":   "2026-04-19 13:00",
		"summary":  "Replace bespoke drawers with property editors and workspace modals.",
	},
	{
		"id":       "queue-106",
		"service":  "schema-tools",
		"owner":    "Infra",
		"priority": "P1",
		"status":   "Ready",
		"window":   "2026-04-19 14:20",
		"summary":  "Ship pinned columns and selectable review flows for dense admin grids.",
	},
}

func seedOrders() []map[string]any {
	customers := []string{
		"Ada Lovelace",
		"Linus Torvalds",
		"Grace Hopper",
		"Ken Thompson",
		"Margaret Hamilton",
		"Barbara Liskov",
		"Donald Knuth",
		"Edsger Dijkstra",
		"Radia Perlman",
		"John Carmack",
		"Guido van Rossum",
		"Leslie Lamport",
		"Sophie Wilson",
		"Anders Hejlsberg",
		"Brendan Eich",
		"Yukihiro Matsumoto",
		"Bjarne Stroustrup",
		"Katie Bouman",
		"Fei-Fei Li",
		"Tim Berners-Lee",
		"Cynthia Dwork",
		"Adele Goldberg",
		"James Gosling",
		"Frances Allen",
		"Carol Shaw",
		"Brian Kernighan",
		"Whitfield Diffie",
		"Martin Fowler",
		"Ward Cunningham",
		"Alan Kay",
	}
	statuses := []string{"queued", "open", "archived", "open", "queued"}
	baseTotal := 42.50
	orders := make([]map[string]any, 0, len(customers))

	for index, customer := range customers {
		orderNumber := 1000 + index + 1
		orders = append(orders, map[string]any{
			"id":       fmt.Sprintf("order-%d", orderNumber),
			"number":   fmt.Sprintf("#%d", orderNumber),
			"customer": customer,
			"status":   statuses[(index+1)%len(statuses)],
			"total":    baseTotal + float64(index+1)*17.35,
		})
	}

	return orders
}
