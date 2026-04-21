# Assignment 5: Fine-Tuning a Language Model Using Two RL Algorithms (GRPO vs. DPO)

import os, json, torch, wandb, numpy as np 
import argparse
import shutil
from datetime import datetime
from datasets import load_dataset, DatasetDict
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import GRPOConfig, GRPOTrainer, DPOTrainer, DPOConfig

# ===============================
# Section 1: Environment Setup (CPU)
# ===============================
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
torch.backends.mps.is_available = lambda: False
device = torch.device("cpu")    # This is forcing the device to CPU
dtype = torch.float32
print(f"🔹 Using device: {device}\n")

# Optional Weights & Biases
try:
    wandb.login()
    wandb_enabled = True
except Exception:
    wandb_enabled = False
    print("Proceeding without wandb.")


# =======================================================
# Section 2 — Dataset Loading functions
# DO NOT MODIFY THESE FUNCTIONS
# =======================================================
def load_GRPO_dataset(ds_name, train_size=2000, val_size=200, test_size=200):
    """
    The Datast we are using is structured for DPO training with preference pairs.
    For GRPO, we need to convert it into a prompt-completion format.
    This function loads the dataset, flattens it, and splits it into train/val
    """
    raw = load_dataset(ds_name)
    ds = raw["train"] if "train" in raw else next(iter(raw.values()))

    def flatten(ex):
        chosen = ex.get("chosen")
        prompt, completion = "", ""
        if isinstance(chosen, list) and isinstance(chosen[0], dict):
            parts = []
            for m in chosen:
                r, c = m.get("role", ""), m.get("content", "")
                if r == "user":
                    parts.append(f"User: {c}")
                elif r == "assistant":
                    parts.append(f"Assistant: {c}")
            joined = "\n".join(parts)
            if "Assistant:" in joined:
                pre, post = joined.rsplit("Assistant:", 1)
                prompt, completion = pre.strip(), post.strip()
        else:
            prompt = ex.get("prompt", "")
            completion = str(chosen)
        return {"prompt": prompt, "completion": completion}

    ds = ds.map(flatten)
    ds = ds.remove_columns([c for c in ds.column_names if c not in ["prompt", "completion"]])
    ds = ds.shuffle(seed=42)
    total = train_size + val_size + test_size
    ds = ds.select(range(min(total, len(ds))))
    
    final_dataset = DatasetDict({
        "train": ds.select(range(train_size)),
        "validation": ds.select(range(train_size, train_size + val_size)),
        "test": ds.select(range(train_size + val_size, total))
    })
    print(f"\n📚 Loaded GRPO dataset: \n{final_dataset}")
    
    return final_dataset


def load_DPO_dataset(ds_name, train_size=2000, val_size=200, test_size=200):
    """
    Load HF preference dataset and create deterministic splits.
    """
    ds      = load_dataset(ds_name)["train"].shuffle(seed=42)
    total   = train_size + val_size + test_size
    ds      = ds.select(range(min(total, len(ds))))

    dsdict  = DatasetDict({
        "train"      : ds.select(range(train_size)),
        "validation" : ds.select(range(train_size,
                                       train_size + val_size)),
        "test"       : ds.select(range(train_size + val_size, total)),
    })
    print(f"\n📚 Loaded DPO dataset\n{dsdict}")
    return dsdict

        
# =======================================================
# Section 3 — GRPO Training and it's reward function
# =======================================================
def reward_len(completions, **kwargs):
    """
    Reward function that encourages completions of length around 50 words.
    Returns a list of float rewards. (one per completion).
    (Autograder will check this output for correctness.)
    """
    # TODO: Implement length-based reward
    pass


def train_grpo(model_id, dataset, output_dir):
    """
    Train GRPO model using length-based reward.
    """
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)          # remove leftovers (old adapters)
    os.makedirs(output_dir, exist_ok=True)

    # ---------- model -----------
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.model_max_length = 2048       
    tokenizer.truncation_side  = "left"                 # cut from the start
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
    model.to(device)
    print("🤖 Base Model loaded successfully")

    # Apply LoRA
    # TODO: Configure LoRA parameters appropriately
    try:
        lora_config = LoraConfig(
            task_type="CAUSAL_LM",
            r=16,               # TODO: 
            lora_alpha=32,      # TODO: 
            target_modules=["q_proj", "v_proj"], 
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        print("Successfully applied LoRA")
    except Exception as e:
        print(f"Error applying LoRA: {e}")
        # Fallback to no LoRA if needed
        print("Continuing without LoRA")

    # ---------- GRPO config -----------
    # TODO: set appropriate parameters for optimizing performance
    training_args = GRPOConfig(
        output_dir=output_dir,
        learning_rate       =5e-5,      # TODO: 
        per_device_train_batch_size=4,  # TODO: 
        gradient_accumulation_steps=2,  
        num_train_epochs=3,             # TODO: 
        max_prompt_length=128,          
        max_completion_length=32,
        num_generations=4,  # Must be more than 2
        logging_steps=10,
        max_grad_norm=0.03,
        fp16=False,
        bf16=False,
        report_to=["wandb"] if wandb_enabled else [],
        remove_unused_columns=False,
        run_name=f"Smol-GRPO-CPU",
    )

    # ---------- trainer ----------
    trainer = GRPOTrainer(
        model=model,
        reward_funcs=[reward_len],
        args=training_args,
        train_dataset=dataset["train"].select(range(len(dataset["train"]))),
    )

    # ---------- train ------------
    if wandb_enabled:
        wandb.init(project="SmolGRPO")
    print("\n🧠 Starting GRPO training...")
    trainer.train()
    print("✅ Training completed")
    
    # Save model
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"✅ Model and tokenizer saved to {output_dir}\n")

    return model, tokenizer


# =======================================================
# Section 4 — DPO Training
# =======================================================
def train_dpo(model_id, dataset, output_dir):
    """
    Train a SmolLM model with Direct Preference Optimisation (DPO)
    using LoRA adapters and save a *merged* checkpoint that can be
    loaded with a plain   AutoModelForCausalLM.from_pretrained(...)
    """
    # --- Setup ---
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # ----- Reference model (frozen) -----
    ref_model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)
    ref_model.to(device)    # Change to "cpu" if doesnt work
    ref_model.eval()
    for p in ref_model.parameters():
        p.requires_grad_(False)
    print("🤖 Reference (frozen) model loaded successfully.")

    # ----- Trainable policy model -----
    policy_model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)
    policy_model.to(device)
    policy_model.config.use_cache = False

    # Apply LoRA
    # TODO: Configure LoRA parameters appropriately
    try:
        lora_cfg = LoraConfig(
            r=16,                  # doubled rank for better adaptation
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],
            bias="none",
            task_type="CAUSAL_LM",
        )
        policy_model = get_peft_model(policy_model, lora_cfg)
        policy_model.enable_input_require_grads()
        policy_model.print_trainable_parameters()
        print("✅ Applied LoRA to policy model.")
    except Exception as e:
        print(f"⚠️ LoRA application failed: {e}")
        print("Continuing without LoRA...")

    # ----- DPO configuration -----
    # TODO: set appropriate parameters for optimizing performance
    dpo_args = DPOConfig(
        output_dir=output_dir,
        learning_rate=5e-5,             # TODO: 
        per_device_train_batch_size=1,  # TODO: 
        gradient_accumulation_steps=2,   
        num_train_epochs=1,             # TODO: 
        max_grad_norm=1.0,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=10,
        report_to=["wandb"] if wandb_enabled else [],
        run_name="Smol-DPO-LoRA32",
        remove_unused_columns=False,
        max_length=256,
        max_prompt_length=256,
    )

    # ---------- trainer ----------
    trainer = DPOTrainer(
        model=policy_model,
        ref_model=ref_model,
        args=dpo_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
    )

    if wandb_enabled:
        wandb.init(project="SmolDPO", name=f"DPO_LoRA32_{datetime.now().strftime('%H%M%S')}")

    print("\n🧠 Starting DPO training…")
    # policy_model.train()
    trainer.beta = 0.2  # strong preference signal
    trainer.train()
    print("✅ DPO training finished.")

    # ----- Merge and save LoRA adapters -----
    print("🔄 Merging LoRA adapters into base weights …")
    merged_model = policy_model.merge_and_unload()
    merged_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"✅ Merged model + tokenizer saved to {output_dir}")

    return merged_model, tokenizer


# =======================================================
# Section 5 — Evaluation Functions
# DO NOT MODIFY THESE FUNCTIONS
# =======================================================
def evaluate_mean_reward(model, tokenizer, dataset, max_samples=10):
    """Compute mean reward of model-generated responses."""
    model.eval()
    rewards = []
    n = min(max_samples, len(dataset["test"]))
    with torch.inference_mode():
        for ex in dataset["test"].select(range(n)):
            prompt = ex["prompt"]
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            output_ids = model.generate(**inputs, max_new_tokens=64, do_sample=True,temperature=0.9,
                                        top_p=0.95,)
            completion = tokenizer.decode(
                output_ids[0], skip_special_tokens=True
            )[len(prompt):]
            rewards.append(reward_len([completion])[0])

    mean_reward = float(np.mean(rewards))
    return mean_reward
    

def evaluate_all(
        grpo_dir: str,
        dpo_dir:  str,
        grpo_ds,
        json_path: str = "evaluation_results.json",
        model_id: str = "HuggingFaceTB/SmolLM-135M-Instruct",
    ):
    
    """
    Load final GRPO & DPO checkpoints (CPU), run both metrics on both
    models, and save a results JSON. Returns the results dict.
    """

    # ----- load base model -------------------------------------------
    print(f"🔹 Loading Base model")
    tok_base = AutoTokenizer.from_pretrained(model_id)
    model_base = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=dtype
    ).to(device)
    
    # ----- load GRPO -------------------------------------------------
    try:
        if not os.path.isdir(grpo_dir):
            raise FileNotFoundError(f"GRPO model not found in {grpo_dir}")
            grpo_non_found = True
        print(f"🔹 Loading GRPO model from {grpo_dir}")
        tok_grpo   = AutoTokenizer.from_pretrained(grpo_dir)
        model_grpo = AutoModelForCausalLM.from_pretrained(
            grpo_dir, torch_dtype=dtype
        ).to(device)
        grpo_non_found = False
    except FileNotFoundError as e:
        print(e)
        grpo_non_found = True
    # ----- load DPO --------------------------------------------------
    try:
        if not os.path.isdir(dpo_dir):
            raise FileNotFoundError(f"DPO model not found in {dpo_dir}")
            dpo_non_found = True
        print(f"🔹 Loading DPO model from {dpo_dir}")
        tok_dpo   = AutoTokenizer.from_pretrained(dpo_dir)
        model_dpo = AutoModelForCausalLM.from_pretrained(
            dpo_dir, torch_dtype=dtype
        ).to(device)    
        dpo_non_found = False
    except FileNotFoundError as e:
        print(e)
        dpo_non_found = True
        
    # ----- evaluate --------------------------------------------------
    print("\n🔍 Evaluating models...")
    base_mean_reward   = evaluate_mean_reward(model_base, tok_base, grpo_ds)
    print(f"✅ BASE – Mean Reward: {base_mean_reward:.4f}")
    
    if grpo_non_found:
        print("GRPO model not found, skipping GRPO evaluation.")
        grpo_mean_reward = -1.0
    else:
        grpo_mean_reward   = evaluate_mean_reward(model_grpo, tok_grpo, grpo_ds)
        print(f"✅ GRPO – Mean Reward: {grpo_mean_reward:.4f}")
        
    if dpo_non_found:
        print("DPO model not found, skipping DPO evaluation.")
        dpo_mean_reward = -1.0
    else:
        dpo_mean_reward    = evaluate_mean_reward(model_dpo, tok_dpo, grpo_ds)
        print(f"✅ DPO – Mean Reward: {dpo_mean_reward:.4f}")
    

    # ----- package & save -------------------------------------------
    results = {
        "Base_mean_reward"        : base_mean_reward,
        "GRPO_mean_reward"        : grpo_mean_reward,
        "DPO_mean_reward"         : dpo_mean_reward,
        "timestamp"               : datetime.now().isoformat(),
    }
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Evaluation complete. Results saved to {json_path}")
    return results


# =======================================================
# Section 6 - Generate Response Function 
# DO NOT MODIFY THIS FUNCTION
# =======================================================
def generate_response(
        model_id: str = "BASE",
        prompt: str = "",
        max_new_tokens: int = 128,
        temperature: float = 0.9,
        top_p: float = 0.95,
        device: str = "cpu",
    ):
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty. Please provide a valid prompt text.")

    # ------- Load model and tokenizer --------
    if model_id == "BASE":
        print(f"\n🔹 Loading Base model")
        tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM-135M-Instruct")
        model = AutoModelForCausalLM.from_pretrained("HuggingFaceTB/SmolLM-135M-Instruct", torch_dtype=torch.float32)
        model.to(device)
        model.eval()
    elif model_id == "GRPO":
        print(f"\n🔹 Loading GRPO model")
        tokenizer = AutoTokenizer.from_pretrained("./GRPO_results/final_model")
        model = AutoModelForCausalLM.from_pretrained("./GRPO_results/final_model", torch_dtype=torch.float32)
        model.to(device)
        model.eval()
    elif model_id == "DPO":
        print(f"\n🔹 Loading DPO model")
        tokenizer = AutoTokenizer.from_pretrained("./DPO_results/final_model")
        model = AutoModelForCausalLM.from_pretrained("./DPO_results/final_model", torch_dtype=torch.float32)
        model.to(device)
        model.eval()

    # ------- Tokenize and generate --------
    print(f"🔹 Getting response from the model")
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    # ------- Decode and show result --------
    input_len = len(inputs["input_ids"][0])
    completion = tokenizer.decode(output_ids[0][input_len:], skip_special_tokens=True)

    print("\n===========================================================")
    print(f"\n🤔 Prompt:\n{prompt}")
    print(f"\n🤖 [{model_id}] Model Response:\n{completion.strip()}")
    print("\n===========================================================")

    return completion.strip()


# =======================================================
# Section 7 - Main 
# DO NOT MODIFY THESE FUNCTIONS
# =======================================================
def main():
    model_id = "HuggingFaceTB/SmolLM-135M-Instruct"
    ds_name = "argilla/ultrafeedback-binarized-preferences-cleaned"
    GRPO_FINAL_DIR = "./GRPO_results/final_model"
    DPO_FINAL_DIR  = "./DPO_results/final_model"

    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=str, choices=["training", "evaluation", "generation"],  default="training")
    parser.add_argument("--algo", type=str, choices=["BASE", "GRPO", "DPO"],  default="GRPO")
    args = parser.parse_args()

    # --------- model training ----------
    if args.run == "training":
        grpo_dataset = load_GRPO_dataset(ds_name)
        dpo_dataset  = load_DPO_dataset(ds_name)

        if args.algo == "GRPO":
            print("🔹 GRPO model training")
            train_grpo(model_id, grpo_dataset, GRPO_FINAL_DIR)
        elif args.algo == "DPO":
            print("🔹 DPO model training")
            train_dpo(model_id, dpo_dataset, DPO_FINAL_DIR)
        else: 
            raise ValueError(f"Unknown algorithm: {args.algo}")
        
    # ----------- evaluate ------------
    elif args.run == "evaluation":
        grpo_dataset = load_GRPO_dataset(ds_name)
        dpo_dataset  = load_DPO_dataset(ds_name)

        evaluate_all(
            GRPO_FINAL_DIR, DPO_FINAL_DIR,
            grpo_dataset,
            json_path="evaluation_results.json",
            model_id=model_id,
        )

    # ----------- generation ------------
    elif args.run == "generation":
        prompt = input("\n📝Enter your prompt: ").strip()
        generate_response(model_id=args.algo, prompt=prompt)


if __name__ == "__main__":
    main()
