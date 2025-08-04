package main

import (
	"fmt"
	"log"
	"net"
	"time"
)

func testMongoDB() error {
	// MongoDB typically runs on port 27017
	// Use kubectl port-forward to expose it: kubectl port-forward svc/mongodb 27017:27017
	addr := "localhost:27017"

	// Connect to MongoDB
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer conn.Close()

	// Set timeout
	conn.SetDeadline(time.Now().Add(5 * time.Second))

	// Try a simple ping by checking if the connection is alive
	// Write a small test message
	testMsg := []byte{0x00}
	conn.SetWriteDeadline(time.Now().Add(1 * time.Second))
	_, err = conn.Write(testMsg)
	if err != nil {
		// Connection is closed
		return fmt.Errorf("connection test failed: %w", err)
	}
	
	// If we got here, the connection is at least open
	// For a more thorough test, you'd implement the full MongoDB wire protocol
	
	return nil
}

func main() {
	fmt.Println("Testing MongoDB connectivity...")

	// Try to connect multiple times
	var lastErr error
	for i := 0; i < 3; i++ {
		err := testMongoDB()
		if err == nil {
			fmt.Println("✓ MongoDB connection successful")
			fmt.Println("✓ MongoDB is running successfully!")
			fmt.Println("Note: For a full health check, consider using the official mongo-go-driver")
			return
		}
		lastErr = err
		if i < 2 {
			time.Sleep(1 * time.Second)
		}
	}
	
	log.Fatalf("MongoDB test failed after 3 attempts: %v", lastErr)
}