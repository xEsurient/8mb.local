// Notification sounds synthesized with Web Audio (soft sine tones with envelopes).
let ctx: AudioContext | null = null;

function getCtx(): AudioContext | null {
  try {
    const AC = window.AudioContext || (window as any).webkitAudioContext;
    if (!AC) return null;
    if (!ctx) ctx = new AC();
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
    return ctx;
  } catch {
    return null;
  }
}

function tone(c: AudioContext, freq: number, start: number, dur: number, peak: number) {
  const osc = c.createOscillator();
  const gain = c.createGain();
  osc.type = 'sine';
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(peak, start + 0.015);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(gain).connect(c.destination);
  osc.start(start);
  osc.stop(start + dur + 0.05);
}

/** Gentle ascending C-E-G chime for job completion. */
export function playSuccessChime(volume = 0.15) {
  const c = getCtx();
  if (!c) return;
  const t = c.currentTime + 0.02;
  [523.25, 659.25, 783.99].forEach((f, i) => tone(c, f, t + i * 0.12, 0.6, volume));
}

/** Two lower tones used to signal an automatic retry. */
export function playRetryTone(volume = 0.12) {
  const c = getCtx();
  if (!c) return;
  const t = c.currentTime + 0.02;
  tone(c, 349.23, t, 0.3, volume);
  tone(c, 349.23, t + 0.25, 0.3, volume);
}
