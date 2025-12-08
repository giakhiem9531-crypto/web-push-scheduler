self.addEventListener("push", event => {
    let data = {};

    try {
        // Dữ liệu từ Python là JSON → parse
        data = event.data ? event.data.json() : {};
    } catch (e) {
        console.error("Push data parse error:", e);
    }

    const title = "Web Push Scheduler";
    const message = data.message || "Bạn có thông báo mới!";

    const options = {
        body: message,
        icon: "/static/icons/icon-192.png",
        badge: "/static/icons/icon-192.png",
        data: {
            url: "/"
        }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener("notificationclick", event => {
    event.notification.close();
    const url = event.notification.data.url || "/";

    event.waitUntil(
        clients.matchAll({ type: "window" }).then(clientsList => {
            for (const client of clientsList) {
                if (client.url === url && "focus" in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});
