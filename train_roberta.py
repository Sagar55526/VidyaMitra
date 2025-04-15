from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, TrainingArguments, Trainer
import torch

# Load dataset (ensure `datasets` is updated)
dataset = load_dataset("squad")

# Load tokenizer and model
model_name = "roberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForQuestionAnswering.from_pretrained(model_name)

# Tokenization function
def preprocess_function(examples):
    return tokenizer(
        examples["question"], 
        examples["context"], 
        truncation=True, 
        padding="max_length", 
        max_length=512, 
        return_overflowing_tokens=False  # To avoid warnings
    )

# Tokenize dataset
tokenized_datasets = dataset.map(preprocess_function, batched=True)

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",  # Fixed deprecated `evaluation_strategy`
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    learning_rate=3e-5,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10
)

# Define trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer
)

# Train the model
if torch.cuda.is_available():
    print("Using GPU for training")
else:
    print("Using CPU for training")

trainer.train()
