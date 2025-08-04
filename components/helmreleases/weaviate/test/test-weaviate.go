package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

func main() {
	// Weaviate typically runs on port 8080
	// Use kubectl port-forward to expose it: kubectl port-forward svc/weaviate 8080:8080
	weaviateURL := "http://localhost:8080"

	fmt.Println("Testing Weaviate connectivity...")

	// Create HTTP client with timeout
	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	// Check if Weaviate is ready
	resp, err := client.Get(weaviateURL + "/v1/.well-known/ready")
	if err != nil {
		log.Fatalf("Failed to connect to Weaviate: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Fatalf("Weaviate is not ready. Status code: %d", resp.StatusCode)
	}

	fmt.Println("✓ Weaviate is ready")

	// Get cluster metadata
	resp, err = client.Get(weaviateURL + "/v1/meta")
	if err != nil {
		log.Printf("Failed to get metadata: %v", err)
		return
	}
	defer resp.Body.Close()

	var meta map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&meta); err != nil {
		log.Printf("Failed to decode metadata: %v", err)
		return
	}

	fmt.Printf("✓ Weaviate version: %v\n", meta["version"])
	fmt.Println("✓ Weaviate is running successfully!")
}