"""Anpassung von Laya Multilingual an die KYC-Entscheidung auf Apple Silicon (MPS).

Angelehnt an das offizielle Skript notebooks/laya_finetune_typed_decisions_mps.py
(github.com/NandhaKishorM/laya): gleiches Modell-Setup, gleicher Verlust
(Kreuzentropie + RL-Term mit proper_reward), Gradient Checkpointing, fp16-Export.

Abweichungen für das KYC-Projekt:
- Basis ist der mehrsprachige Checkpoint, Daten sind unsere KYC-Fälle (nur `train`).
- Modellauswahl je Epoche und Temperaturkalibrierung ausschließlich auf `validation`.
- `test` wird hier nicht angefasst.

Beispiele:
    python kyc_train.py --probe 64          # Speicher und Laufzeit messen
    python kyc_train.py --epochs 3
"""
import argparse
import hashlib
import json
import math
import random
import shutil
import time
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file
from transformers import AutoTokenizer

from laya.agent import _fix_tokenizer_config
from laya.common import build_model, clamp_temperature, proper_reward

import kyc_data as K

OUTPUT_DIR = K.PROJECT_DIR / "modelle" / "laya-multilingual-kyc"


def log(message, log_file):
    line = time.strftime("%H:%M:%S ") + message
    print(line, flush=True)
    with open(log_file, "a") as f:
        f.write(line + "\n")


def save_checkpoint(model, tokenizer, cfg, path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    weights = {n: v.detach().half().cpu().contiguous() for n, v in model.state_dict().items()}
    save_file(weights, str(path / "model.safetensors"))
    model.encoder.config.save_pretrained(path / "encoder")
    tokenizer.save_pretrained(path / "tokenizer")
    (path / "rl_agent_config.json").write_text(json.dumps(cfg, indent=2))


def validation_metrics(logits, items, customers):
    probs = torch.softmax(logits, -1)
    gold = torch.tensor([it["label"] for it in items])
    pred = probs.argmax(1)
    nll = -torch.log(probs[torch.arange(len(gold)), gold].clamp_min(1e-12)).mean().item()
    needs_review = torch.tensor([c["sollbewertung"]["manuelle_pruefung_erforderlich"] for c in customers])
    green = torch.tensor([not K.has_rule_trigger(c["eingabe"]) for c in customers])
    auto_release = green & (pred == K.OPTIONS.index("keine_manuelle_pruefung"))
    return {
        "nll": round(nll, 4),
        "genauigkeit_3_klassen": round((pred == gold).float().mean().item(), 4),
        "faelschlich_freigegeben": int((needs_review & auto_release).sum()),
        "unnoetig_manuell": int((~needs_review & ~auto_release).sum()),
    }


def fit_temperature(logits, labels):
    """Eine Temperatur für die Choice-Frage, per LBFGS auf der Validierungs-NLL."""
    log_t = torch.zeros(1, requires_grad=True)
    optimizer = torch.optim.LBFGS([log_t], lr=0.1, max_iter=200)

    def closure():
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(logits / log_t.exp(), labels)
        loss.backward()
        return loss

    optimizer.step(closure)
    # Laya wendet nur Temperaturen in [TEMP_MIN, TEMP_MAX] an. Bei (nahezu) fehlerfreier
    # Validierung liefe das Optimum gegen 0, also gegen beliebig scharfe Wahrscheinlichkeiten.
    return clamp_temperature(float(log_t.exp().item()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--micro-batch", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lr-encoder", type=float, default=2.5e-5)
    ap.add_argument("--lr-head", type=float, default=1e-4)
    ap.add_argument("--head-only", action="store_true", help="Encoder einfrieren, nur Entscheidungsteil trainieren")
    ap.add_argument("--probe", type=int, default=0, help="Nur N Trainingsfälle, keine Ausgabe")
    ap.add_argument("--data", default=str(K.DATA_FILE), help="Datensatz (JSON mit kunden)")
    ap.add_argument("--ce-only", action="store_true", help="Nur Kreuzentropie, ohne RL-Term (stabiler bei schwer trennbaren Daten)")
    ap.add_argument("--init", help="Gewichte aus diesem Checkpoint statt aus dem Basismodell laden (Weitertraining)")
    ap.add_argument("--output", default=str(OUTPUT_DIR))
    ap.add_argument("--device", default="mps")
    ap.add_argument("--seed", type=int, default=20261003)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device(args.device if args.device != "mps" or torch.backends.mps.is_available() else "cpu")
    output_dir = Path(args.output)
    work_dir = output_dir.parent / (output_dir.name + "_arbeit")
    work_dir.mkdir(parents=True, exist_ok=True)
    log_file = work_dir / "training.log"

    base = K.BASE_MODEL
    _fix_tokenizer_config(str(base))
    cfg = json.loads((base / "rl_agent_config.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(base / "tokenizer")

    customers = K.load_customers(args.data)
    train_customers = [c for c in customers if c["metadaten"]["split"] == "train"]
    val_customers = [c for c in customers if c["metadaten"]["split"] == "validation"]
    if args.probe:
        train_customers = random.Random(args.seed).sample(train_customers, args.probe)
        val_customers = val_customers[:32]
    train_items = K.build_items(tokenizer, train_customers, cfg["max_len"], cfg["head_max_len"])
    val_items = K.build_items(tokenizer, val_customers, cfg["max_len"], cfg["head_max_len"])
    log(f"Device {device}; train {len(train_items)}, validation {len(val_items)}; "
        f"micro_batch {args.micro_batch}, grad_accum {args.grad_accum}, epochen {args.epochs}, "
        f"nur_kopf {args.head_only}", log_file)

    model = build_model(cfg, encoder_dir=base / "encoder")
    init_weights = Path(args.init) / "model.safetensors" if args.init else base / "model.safetensors"
    model.load_state_dict(load_file(str(init_weights)), strict=True)
    model.float()
    if args.head_only:
        for p in model.encoder.parameters():
            p.requires_grad_(False)
    else:
        model.encoder.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.head_checkpointing = True
    model.to(device)

    encoder_params = [p for n, p in model.named_parameters() if n.startswith("encoder.") and p.requires_grad]
    head_params = [p for n, p in model.named_parameters() if not n.startswith("encoder.")]
    groups = [{"params": head_params, "lr": args.lr_head}]
    if encoder_params:
        groups.append({"params": encoder_params, "lr": args.lr_encoder})
    optimizer = torch.optim.AdamW(groups, weight_decay=0.01)
    updates = max(1, math.ceil(len(train_items) / args.micro_batch / args.grad_accum) * args.epochs)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=updates, eta_min=1e-6)

    before = validation_metrics(K.option_logits(model, val_items, tokenizer.pad_token_id, device), val_items, val_customers)
    log(f"Validation vor Training: {before}", log_file)

    best = None
    history = [{"epoche": 0, **before}]
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        random.Random(args.seed + epoch).shuffle(train_items)
        sigma = 0.4 + (0.1 - 0.4) * epoch / max(1, args.epochs - 1)
        optimizer.zero_grad(set_to_none=True)
        ce_sum, steps = 0.0, 0
        for start in range(0, len(train_items), args.micro_batch):
            batch = K.collate(train_items[start:start + args.micro_batch], tokenizer.pad_token_id)
            batch = {k: v.to(device) for k, v in batch.items()}
            mask, target = batch["marker_mask"], batch["target"]
            logits, act = model(batch["input_ids"], batch["attention_mask"], batch["marker_pos"], mask,
                                batch["qtype"], detach_encoder=args.head_only)
            logits = logits.float()

            # RL-Term wie im offiziellen Skript: verrauschte Logits, proper_reward als Belohnung.
            k = mask.sum(-1, keepdim=True).float()
            eps = torch.randn((4,) + logits.shape, device=device) * sigma * mask
            eps = (eps - eps.sum(-1, keepdim=True) / k) * mask
            noisy = logits.detach().unsqueeze(0) + eps
            probs = torch.softmax(noisy.masked_fill(~mask, -1e4), -1)
            with torch.no_grad():
                reward = proper_reward(probs, target.unsqueeze(0), batch["qtype"], mask, w_sph=0.75, w_rps=1.0)
                centered = reward - reward.mean(0, keepdim=True)
                advantage = centered / (centered.std() + 1e-6)
            logp = -(((noisy - logits.unsqueeze(0)) ** 2) * mask).sum(-1) / (2 * sigma ** 2)
            loss_rl = -(advantage * logp).mean()
            loss_ce = -(target * torch.log_softmax(logits.masked_fill(~mask, -1e4), -1)).sum(-1).mean()
            loss = ((0.0 if args.ce_only else loss_rl) + loss_ce + 0.0 * act.sum()) / args.grad_accum
            loss.backward()

            steps += 1
            ce_sum += loss_ce.item()
            if steps % args.grad_accum == 0 or start + args.micro_batch >= len(train_items):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
            if steps % 50 == 0:
                progress = (start + args.micro_batch) / len(train_items)
                log(f"Epoche {epoch + 1}: {progress:.0%}, CE {ce_sum / steps:.4f}, "
                    f"{(time.time() - t0) / 60:.1f} min seit Start", log_file)

        val = validation_metrics(K.option_logits(model, val_items, tokenizer.pad_token_id, device), val_items, val_customers)
        history.append({"epoche": epoch + 1, "train_ce": round(ce_sum / steps, 4), **val})
        log(f"Epoche {epoch + 1} fertig: train CE {ce_sum / steps:.4f}; validation {val}", log_file)
        if args.probe:
            continue
        # Auswahl: wenigste Pfadfehler auf Validierung, bei Gleichstand niedrigere NLL.
        key = (val["faelschlich_freigegeben"] + val["unnoetig_manuell"], val["nll"])
        if best is None or key < best[0]:
            best = (key, epoch + 1)
            save_checkpoint(model, tokenizer, cfg, work_dir / "bester_checkpoint")
            log(f"  -> bester Checkpoint (Epoche {epoch + 1})", log_file)

    minutes = (time.time() - t0) / 60
    if args.probe:
        memory = torch.mps.driver_allocated_memory() / 2**30 if device.type == "mps" else float("nan")
        log(f"Probelauf fertig: {minutes:.1f} min für {len(train_items)} Fälle x {args.epochs} Epochen, "
            f"MPS-Speicher {memory:.1f} GB", log_file)
        return

    # Temperatur auf Validierung kalibrieren, mit dem besten Checkpoint (fp16-Gewichte wie im Betrieb).
    best_weights = load_file(str(work_dir / "bester_checkpoint" / "model.safetensors"))
    model.load_state_dict({k: v.float() for k, v in best_weights.items()})
    model.to(device)
    val_logits = K.option_logits(model, val_items, tokenizer.pad_token_id, device)
    labels = torch.tensor([it["label"] for it in val_items])
    temperature = fit_temperature(val_logits, labels)

    new_cfg = dict(cfg)
    new_cfg.update({
        "model_name": "laya-multilingual-kyc-demo",
        "fine_tuned": True,
        "temperature": [temperature, 1.0, 1.0],
        "temperature_by_options": {},
        "kyc_training": {
            "basis": "convaiinnovations/laya-multilingual" + (f" (weitertrainiert ab {Path(args.init).name})" if args.init else ""),
            "daten": f"{Path(args.data).name} (split train)",
            "daten_sha256": hashlib.sha256(Path(args.data).read_bytes()).hexdigest(),
            "optionen": K.OPTIONS,
            "beste_epoche": best[1],
            "epochen": args.epochs,
            "micro_batch": args.micro_batch,
            "grad_accum": args.grad_accum,
            "lr_encoder": None if args.head_only else args.lr_encoder,
            "lr_kopf": args.lr_head,
            "nur_kopf": args.head_only,
            "nur_kreuzentropie": args.ce_only,
            "seed": args.seed,
            "dauer_minuten": round(minutes, 1),
            "temperatur_kalibriert_auf": "validation",
            "verlauf_validation": history,
        },
    })
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(work_dir / "bester_checkpoint", output_dir)
    (output_dir / "rl_agent_config.json").write_text(json.dumps(new_cfg, indent=2, ensure_ascii=False))
    log(f"Fertig nach {minutes:.1f} min. Beste Epoche {best[1]}, Temperatur {temperature:.3f}. "
        f"Modell: {output_dir}", log_file)


if __name__ == "__main__":
    main()
