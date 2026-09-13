const CHIME_PREF_KEY = "dd-waiting-room-chime";

export function isArrivalChimeEnabled(): boolean {
  if (typeof window === "undefined") return false;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return false;
  }
  return localStorage.getItem(CHIME_PREF_KEY) !== "off";
}

/**
 * Soft two-tone cue for remote "Patient arrived" events.
 * No-op when reduced motion is on or the staff preference is off.
 */
export function playArrivalChime(): void {
  if (!isArrivalChimeEnabled()) return;

  try {
    const AudioCtx =
      window.AudioContext ||
      (
        window as unknown as {
          webkitAudioContext?: typeof AudioContext;
        }
      ).webkitAudioContext;
    if (!AudioCtx) return;

    const ctx = new AudioCtx();
    const now = ctx.currentTime;

    const playTone = (freq: number, start: number, duration: number) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.exponentialRampToValueAtTime(0.04, start + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(start);
      osc.stop(start + duration + 0.02);
    };

    playTone(660, now, 0.12);
    playTone(880, now + 0.14, 0.16);

    window.setTimeout(() => {
      void ctx.close();
    }, 500);
  } catch {
    /* autoplay / AudioContext blocked — silent fallback */
  }
}
