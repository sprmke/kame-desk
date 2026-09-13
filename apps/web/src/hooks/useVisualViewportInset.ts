import { useEffect, useState } from "react";

/** Keyboard overlap below the layout viewport. Use on bottom sheets. */
export function useVisualViewportBottomInset(): number {
  const [inset, setInset] = useState(0);

  useEffect(() => {
    const viewport = window.visualViewport;
    if (!viewport) return;

    function update() {
      const current = window.visualViewport;
      if (!current) return;
      const next = window.innerHeight - current.height - current.offsetTop;
      setInset(Math.max(0, Math.round(next)));
    }

    update();
    viewport.addEventListener("resize", update);
    viewport.addEventListener("scroll", update);
    return () => {
      viewport.removeEventListener("resize", update);
      viewport.removeEventListener("scroll", update);
    };
  }, []);

  return inset;
}
