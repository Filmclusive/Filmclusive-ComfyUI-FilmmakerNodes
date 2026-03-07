import { app } from "../../scripts/app.js";

function findWidget(node, widgetName) {
  const widgets = Array.isArray(node?.widgets) ? node.widgets : [];
  return widgets.find((w) => w?.name === widgetName) || null;
}

function setWidgetLabel(node, widgetName, label) {
  const w = findWidget(node, widgetName);
  if (!w) return;
  w.label = label;
}

function setInputLabel(node, inputName, label) {
  const inputs = Array.isArray(node?.inputs) ? node.inputs : [];
  const inp = inputs.find((i) => i?.name === inputName) || null;
  if (!inp) return;
  if ("label" in inp) inp.label = label;
  else inp.name = label;
}

function relabelKSampler(node) {
  setInputLabel(node, "model", "Model");
  setInputLabel(node, "positive", "Prompt (Positive)");
  setInputLabel(node, "negative", "Prompt (Negative)");
  setInputLabel(node, "latent_image", "Latent (Start Frame)");

  setWidgetLabel(node, "seed", "Seed (Randomness)");
  setWidgetLabel(node, "steps", "Sampling Steps");
  setWidgetLabel(node, "cfg", "Prompt Strength (CFG)");
  setWidgetLabel(node, "sampler_name", "Sampler");
  setWidgetLabel(node, "scheduler", "Scheduler");
  setWidgetLabel(node, "denoise", "Effect Strength (Denoise)");
}

function relabelWanVideoSampler(node) {
  setInputLabel(node, "model", "Model");
  setInputLabel(node, "image_embeds", "Reference Image Embeds");
  setInputLabel(node, "text_embeds", "Prompt Embeds");
  setInputLabel(node, "samples", "Latent (Optional Start)");

  // Best-effort renames: only touch widgets that exist.
  setWidgetLabel(node, "seed", "Seed (Randomness)");
  setWidgetLabel(node, "steps", "Sampling Steps");
  setWidgetLabel(node, "cfg", "Prompt Strength (CFG)");
  setWidgetLabel(node, "sampler", "Sampler");
  setWidgetLabel(node, "sampler_name", "Sampler");
  setWidgetLabel(node, "scheduler", "Scheduler");
  setWidgetLabel(node, "denoise", "Effect Strength (Denoise)");
}

function relabelWanVideoModelLoader(node) {
  setInputLabel(node, "lora", "LoRA Stack");
  setWidgetLabel(node, "model_name", "Model File");
}

function relabelWanVideoTextEncode(node) {
  setWidgetLabel(node, "positive", "Prompt (Positive)");
  setWidgetLabel(node, "negative", "Prompt (Negative)");
  setWidgetLabel(node, "text", "Prompt");
}

function relabelWanVideoDecode(node) {
  setInputLabel(node, "vae", "VAE");
  setInputLabel(node, "samples", "Latent (Samples)");
}

app.registerExtension({
  name: "filmclusive.filmmaker_wrapped_nodes",
  nodeCreated(node) {
    const type = String(node?.type || "");
    if (type === "FilmclusiveKSamplerFilmmaker") relabelKSampler(node);
    if (type === "FilmclusiveWanVideoSamplerFilmmaker") relabelWanVideoSampler(node);
    if (type === "FilmclusiveWanVideoModelLoaderFilmmaker") relabelWanVideoModelLoader(node);
    if (type === "FilmclusiveWanVideoTextEncodeCachedFilmmaker") relabelWanVideoTextEncode(node);
    if (type === "FilmclusiveWanVideoDecodeFilmmaker") relabelWanVideoDecode(node);
  },
});

