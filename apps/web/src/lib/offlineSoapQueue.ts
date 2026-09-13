const DB_NAME = "doctordesk-offline";
const DB_VERSION = 1;
const STORE_NAME = "soap-drafts";

export type QueuedSoapDraft = {
  clientDraftToken: string;
  appointmentId: string;
  body: Record<string, unknown>;
  queuedAt: string;
};

function hasIndexedDb(): boolean {
  return typeof indexedDB !== "undefined";
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "clientDraftToken" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function withStore<T>(
  mode: IDBTransactionMode,
  fn: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const db = await openDb();
  try {
    return await new Promise<T>((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, mode);
      const store = tx.objectStore(STORE_NAME);
      const req = fn(store);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  } finally {
    db.close();
  }
}

export function generateClientDraftToken(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `offline-${crypto.randomUUID()}`;
  }
  return `offline-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export async function enqueueSoapDraft(entry: QueuedSoapDraft): Promise<void> {
  if (!hasIndexedDb()) return;
  await withStore("readwrite", (store) => store.put(entry));
}

export async function listQueuedSoapDrafts(): Promise<QueuedSoapDraft[]> {
  if (!hasIndexedDb()) return [];
  const result = await withStore<QueuedSoapDraft[]>("readonly", (store) =>
    store.getAll(),
  );
  return result ?? [];
}

export async function removeQueuedSoapDraft(
  clientDraftToken: string,
): Promise<void> {
  if (!hasIndexedDb()) return;
  await withStore("readwrite", (store) => store.delete(clientDraftToken));
}
