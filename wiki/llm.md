# LLM

<h2>Table of contents</h2>

- [What is an LLM](#what-is-an-llm)
- [Token](#token)
- [Context window](#context-window)
- [Prompt](#prompt)
- [Model](#model)

## What is an LLM

An LLM (Large Language Model) is a type of AI model trained on large amounts of text data that can understand and generate human-readable text, including code.

LLMs power [coding agents](./coding-agents.md#what-is-a-coding-agent) that help you complete tasks in this course.

Docs:

- [What is a large language model?](https://aws.amazon.com/what-is/large-language-model/)

## Token

A token is a unit of text that an LLM processes — roughly a word or a few characters.

LLMs read and generate text token by token. The number of tokens in a message affects how much of the [context window](#context-window) it uses.

## Context window

The context window is the maximum amount of text (measured in [tokens](#token)) that an LLM can process in a single interaction — including the conversation history, files, and the current message.

When the context window is full, earlier parts of the conversation are dropped. To avoid this, keep conversations focused and start a new conversation when switching tasks.

## Prompt

A prompt is the input text you send to an LLM to guide its response.

A clear and specific prompt produces better results. When using a [coding agent](./coding-agents.md#what-is-a-coding-agent), describe what you want to achieve, not just what to do — include relevant file names, error messages, and acceptance criteria.

## Model

A model is a specific trained version of an LLM, identified by a name (e.g., `Qwen3-Coder`, `claude-sonnet-4-6`).

Different models vary in capability, speed, and cost. [Coding agents](./coding-agents.md#choose-a-coding-agent) let you choose which model to use.
