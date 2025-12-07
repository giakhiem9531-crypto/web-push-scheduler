self.addEventListener('push', function(event) {
    let data = 'Bạn có thông báo mới!';
    if (event.data) {
        try {
            const json = event.data.json();
            data = json.message || data;
        } catch (e) {
            data = event.data.text();
        }
    }

    const options = {
        body: data,
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-192.png',
        data: { url: '/' },
        requireInteraction: true
    };

    event.waitUntil(
        self.registration.showNotification('Web Push Scheduler', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    const url = event.notification.data?.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
            for (let client of windowClients) {
                if (client.url === url && 'focus' in client) return client.focus();
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});
