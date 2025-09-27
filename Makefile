.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  install-environment-variables: Launch the script that is responsible for setting up the environment variables"
	@echo "  run-template-migrations: Launch the script that is responsible for installing the templates in the MongoDB database"
	@echo "  instance-configurations: Expose the instance configurations"
	@echo "  setup-docker-in-ubuntu: Launch the script that is responsible for setting up Docker in Ubuntu"
	@echo "  run-postgres-migrations: Run the Postgres migrations"
	@echo "  configure-domains: Configure the service domains in the .env files"
	@echo "  help: Show this help message"

.PHONY: initialize_mongodb
initialize_mongodb:
	@echo "DEPRECATED: Use 'make run-template-migrations' instead" && exit 1

.PHONY: install-environment-variables
install-environment-variables:
	@echo "Installing environment variables..."
	@cd scripts/environment_variables && \
		chmod +x initialize_variables.sh && \
		./initialize_variables.sh
	@echo "Environment variables installed successfully"

.PHONY: configure-domains
configure-domains:
	@echo "Configuring service domains in .env files..."
	@cd scripts/environment_variables && \
		chmod +x update_urls.sh && \
		./update_urls.sh
	@echo "Service domains configured successfully."

.PHONY: start-supabase
start-supabase:
	@echo "Starting Supabase..."
	docker compose up studio kong auth rest realtime storage imgproxy meta functions analytics db vector supavisor

.PHONY: stop-supabase
stop-supabase:
	@echo "Stopping Supabase..."
	docker compose stop studio kong auth rest realtime storage imgproxy meta functions analytics db vector supavisor
	@echo "Supabase stopped successfully"

.PHONY: setup-docker-in-ubuntu
setup-docker-in-ubuntu:
	@echo "Setting up Docker in Ubuntu..."
	@cd scripts/docker && \
		chmod +x ubuntu_server_pre_setup.sh && \
		./ubuntu_server_pre_setup.sh
	@echo "Docker setup in Ubuntu completed successfully"

.PHONY: run-postgres-migrations
run-postgres-migrations:
	@echo "Running Postgres migrations..."
	docker compose exec stackend bash -c "cd infra/migrations/postgres && alembic upgrade head"
	@echo "Postgres migrations completed successfully"

.PHONY: run-template-migrations
run-template-migrations:
	@echo "Running template migrations..."
	docker compose exec stackend bash -c "python scripts/on-premise/insert_stackai_project_templates.py"
	@echo "Template migrations completed successfully"

.PHONY: start-stackai
start-stackai:
	docker compose up -d stackweb stackend celery_worker stackrepl storage

.PHONY: stop-stackai
stop-stackai:
	docker compose down stackweb stackend celery_worker stackrepl storage

.PHONY: secrets
secrets:
	@echo "Secrets:"
	@cd scripts/environment_variables && \
		chmod +x scripts/environment_variables/secrets.sh && \
		./scripts/environment_variables/secrets.sh

# ==================================================================================================
#                                        UPDATE REPOSITORY
# ==================================================================================================
.PHONY: pull
pull: ## Pull and update the local repository using the Python-based ZIP download method.
	@echo "Starting repository update process..."
	@chmod +x scripts/pull/run_puller.sh
	@./scripts/pull/run_puller.sh
	@echo chmod +x scripts/**/*.sh
	@echo "Update process finished. See script output for details."

.PHONY: update
update:
	@echo "Updating repository..."
	@make pull
	@make stop-stackai
	@make install-environment-variables
	docker compose pull stackweb stackend celery_worker stackrepl storage
	docker compose build stackweb stackrepl
	@make start-stackai
	docker compose exec stackend bash -c "cd infra/migrations/postgres && alembic upgrade head"
