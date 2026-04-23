#!/bin/bash
#
# PHANTOM 3B Fine-tuning Training Script
# Creates a new PHANTOM LLM from Llama 3.1 3B base model
#
# Requirements: 
#   - GPU with 12GB+ VRAM (24GB recommended for 3B fine-tune)
#   - Python 3.10+
#   - Ollama or transformers + unsloth
#
# Usage: bash train_phantom.sh

set -e

echo "=== PHANTOM 3B Training ==="
echo "Building your own cybersecurity assistant..."

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: NVIDIA GPU required for training"
    exit 1
fi

echo "GPU detected:"
nvidia-smi --query-gpu=name,memory.total --format=csv

# Install dependencies
echo "Installing dependencies..."
pip install -q torch transformers accelerate datasets peft scipy bitsandbytes unsloth wandb

# Convert dataset to training format
echo "Preparing training data..."
python3 << 'EOF'
import json

with open("data/phantom_train.jsonl", "r") as f:
    lines = f.readlines()

data = []
for line in lines:
    item = json.loads(line)
    text = f"""Instruction: {item['instruction']}
Input: {item['input'] if item['input'] else 'N/A'}
Output: {item['output']}"""
    data.append({"text": text})

with open("data/phantom_train.jsonl", "w") as f:
    for item in data:
        f.write(json.dumps(item) + "\n")

print(f"Prepared {len(data)} training examples")
EOF

# Start training
echo "Starting fine-tuning training..."
python3 << 'EOF'
import os
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model

# Config
MODEL_NAME = "/meta-llama/Llama-3.1-3B-Instruct"  # or 3B base
OUTPUT_DIR = "./phantom_model"

# Load model
print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Load data
dataset = load_dataset("json", data_files="data/phantom_train.jsonl")["train"]

def tokenize(examples):
    return tokenizer(examples["text"], truncation=True, max_length=2048, padding="max_length")

dataset = dataset.map(tokenize, batched=True)

# Training args
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    warmup_steps=100,
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

print("Training PHANTOM 3B...")
trainer.train()

print("Saving model...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"PHANTOM 3B training complete! Model saved to {OUTPUT_DIR}")
EOF

echo ""
echo "=== Training Complete ==="
echo "Your PHANTOM 3B model is ready at: ./phantom_model"
echo ""
echo "To use with Ollama:"
echo "  1. Convert to GGUF: llama.cpp --convert phantom_model"
echo "  2. Create Ollama model: ollama create phantom -f phantom.Modelfile"