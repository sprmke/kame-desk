// Phase 36: read-only offline cache for today's schedule (appointments list)
// and the patient roster (patients list) only. Network-first with a cache
// fallback — every successful online fetch refreshes the cache (so it's
// never more than one request stale), and a failed fetch (offline) serves
// the last cached response instead of a hard error. Nothing else is cached:
// booking/billing/prescription writes and every other GET always hit the
// network, per the read-only-cache production default in
// docs/architecture/messaging-channels.md's sibling doc for this phase.
const API_CACHE_NAME = "doctordesk-api-cache-v1";

self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== API_CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

function isCacheableApiRequest(request) {
  if (request.method !== "GET") return false;
  let url;
  try {
    url = new URL(request.url);
  } catch {
    return false;
  }
  return (
    url.pathname.endsWith("/appointments") || url.pathname.endsWith("/patients")
  );
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!isCacheableApiRequest(request)) return;

  event.respondWith(
    (async () => {
      const cache = await caches.open(API_CACHE_NAME);
      try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
          await cache.put(request, networkResponse.clone());
        }
        return networkResponse;
      } catch (err) {
        const cached = await cache.match(request);
        if (cached) return cached;
        throw err;
      }
    })(),
  );
});

self.addEventListener("push", (event) => {
  let payload = {
    title: "DoctorDesk",
    body: "New alert",
    href: "/dashboard/notifications",
  };
  try {
    if (event.data) payload = { ...payload, ...event.data.json() };
  } catch {
    /* use defaults */
  }
  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      data: { href: payload.href },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const href = event.notification.data?.href || "/dashboard/notifications";
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients) => {
        for (const client of clients) {
          if ("focus" in client) {
            client.navigate(href);
            return client.focus();
          }
        }
        if (self.clients.openWindow) return self.clients.openWindow(href);
      }),
  );
});
