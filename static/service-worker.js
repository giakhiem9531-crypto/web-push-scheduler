self.addEventListener('push', function(event) {
    const data = event.data ? JSON.parse(event.data.text()) : { message: 'Bạn có thông báo mới!' };

    const options = {
        body: data.message,
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-192.png',
        data: { url: '/' }
    };

    event.waitUntil(
        self.registration.showNotification('Web Push Scheduler', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    const url = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            for (let client of windowClients) {
                if (client.url === url && 'focus' in client) return client.focus();
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});
