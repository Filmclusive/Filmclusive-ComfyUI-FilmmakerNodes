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

function slotLabel(node, slotKey, fallback) {
  const w = findWidget(node, `${slotKey}_label`);
  const v = String(w?.value ?? "").trim();
  return v || fallback;
}

function updateSlotLabels(node) {
  const slots = [
    ["style", "Style / Look"],
    ["character_1", "Character 1"],
    ["character_2", "Character 2"],
    ["character_3", "Character 3"],
    ["prop", "Hero Prop"],
    ["lighting", "Lighting"],
    ["camera", "Camera"],
    ["set_design", "Set Design"],
  ];

  for (const [slotKey, fallback] of slots) {
    const label = slotLabel(node, slotKey, fallback);
    setWidgetLabel(node, `${slotKey}_label`, `${fallback} Label`);
    setWidgetLabel(node, `${slotKey}_lora`, `${label} LoRA`);
    setWidgetLabel(node, `${slotKey}_strength`, `${label} Strength`);
  }
}

function attachLabelCallbacks(node) {
  const slots = ["style", "character_1", "character_2", "character_3", "prop", "lighting", "camera", "set_design"];
  for (const slotKey of slots) {
    const w = findWidget(node, `${slotKey}_label`);
    if (!w) continue;
    const prev = w.callback;
    w.callback = function (...args) {
      try {
        updateSlotLabels(node);
        app?.graph?.setDirtyCanvas?.(true, true);
        app?.canvas?.setDirty?.(true, true);
      } finally {
        if (typeof prev === "function") return prev.apply(this, args);
      }
    };
  }
}

app.registerExtension({
  name: "filmclusive.filmmaker_multi_lora",
  nodeCreated(node) {
    const type = String(node?.type || "");
    if (type !== "FilmclusiveMultiLoRAFilmmaker") return;
    updateSlotLabels(node);
    attachLabelCallbacks(node);
  },
});

