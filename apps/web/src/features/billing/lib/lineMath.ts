export function lineAmount(quantity: string, unitPrice: string): string {
  const q = Number(quantity);
  const p = Number(unitPrice);
  if (!Number.isFinite(q) || !Number.isFinite(p) || q <= 0 || p < 0) {
    return "0.00";
  }
  return (Math.round(q * p * 100) / 100).toFixed(2);
}

export function sumLines(
  rows: Array<{ quantity: string; unit_price: string }>,
): string {
  const total = rows.reduce(
    (acc, row) => acc + Number(lineAmount(row.quantity, row.unit_price)),
    0,
  );
  return total.toFixed(2);
}
