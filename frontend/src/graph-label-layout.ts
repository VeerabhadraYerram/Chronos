export type Rect = { x: number; y: number; width: number; height: number };
export type LabelAnchor = Rect & { id: string };

export function intersects(a: Rect, b: Rect, gap = 10): boolean {
  return (
    a.x < b.x + b.width + gap &&
    a.x + a.width + gap > b.x &&
    a.y < b.y + b.height + gap &&
    a.y + a.height + gap > b.y
  );
}

/** Reserve measured rectangles in stable order. Expand the search until a free
 * slot exists: dense graphs get more canvas space, never stacked labels. */
export function placeLabels(
  anchors: LabelAnchor[],
  obstacles: Rect[],
): LabelAnchor[] {
  const occupied = [...obstacles];
  return [...anchors]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((anchor) => {
      const stepX = anchor.width + 24,
        stepY = anchor.height + 24;
      for (let ring = 0; ; ring++) {
        const candidates: { dx: number; dy: number }[] = [];
        for (let dx = -ring; dx <= ring; dx++) {
          for (let dy = -ring; dy <= ring; dy++) {
            if (Math.max(Math.abs(dx), Math.abs(dy)) === ring)
              candidates.push({ dx, dy });
          }
        }
        candidates.sort(
          (a, b) =>
            (a.dx * stepX) ** 2 +
            (a.dy * stepY) ** 2 -
            (b.dx * stepX) ** 2 -
            (b.dy * stepY) ** 2,
        );
        for (const { dx, dy } of candidates) {
          const candidate = {
            ...anchor,
            x: anchor.x + dx * stepX,
            y: anchor.y + dy * stepY,
          };
          if (occupied.every((rect) => !intersects(candidate, rect))) {
            occupied.push(candidate);
            return candidate;
          }
        }
      }
    });
}
