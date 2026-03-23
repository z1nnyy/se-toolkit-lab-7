# Bot Development Plan

We will build the bot in four stages that match the required tasks. First, we create a testable scaffold with a CLI `--test` mode so command logic can run without Telegram. The entry point stays responsible for parsing input and later starting the Telegram transport, while handlers remain plain Python functions that accept arguments and return text. Configuration is loaded from `.env.bot.secret` so secrets and service URLs stay outside the code.

Second, we connect the bot to the LMS backend. We will add a dedicated API client in `bot/services/` that uses bearer authentication with `LMS_API_KEY` and reads the backend URL from configuration. Command handlers such as `/health`, `/labs`, and `/scores` will call this client and return friendly text. Errors like connection failures or backend downtime will be converted into user-facing messages instead of crashes.

Third, we add intent-based natural language routing with an LLM. The bot will expose backend actions as tool definitions and let the model choose which tool to call for plain-language questions. The fallback path should only handle real LLM outages, not replace routing with keyword matching.

Fourth, we package the bot for deployment. We will add a Dockerfile, connect the bot to `docker-compose.yml`, document environment variables and deployment steps, and verify the bot both in CLI test mode and in Telegram on the VM.
