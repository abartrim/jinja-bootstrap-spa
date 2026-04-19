package main

import (
	"log"
	"net/http"
	"os"
)

func main() {
	app, err := newExampleApp()
	if err != nil {
		log.Fatalf("create go example app: %v", err)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "5001"
	}

	addr := "127.0.0.1:" + port
	log.Printf("jinja-bootstrap-spa Go example listening on http://%s", addr)
	if err := http.ListenAndServe(addr, app.routes()); err != nil {
		log.Fatalf("serve go example app: %v", err)
	}
}
