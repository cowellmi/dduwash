const statuses = [
    {
        'img': '/img/green.svg',
        'alt': {
            'en': 'green circle',
            'es': 'círculo verde',
        },
        'text': {
            'en': 'Empty',
            'es': 'Vacío',
        },
    },
    {
        'img': '/img/red.svg',
        'alt': {
            'en': 'red circle',
            'es': 'círculo rojo',
        },
        'text': {
            'en': 'Occupied',
            'es': 'Ocupado',
        },
    },
    {
        'img': '/img/yellow.svg',
        'alt': {
            'en': 'yellow circle',
            'es': 'círculo amarillo',
        },
        'text': {
            'en': 'Maintenance',
            'es': 'Mantenimiento',
        },
    },
];

(async () => {
    try {
        // Cache status images
        for (const status of statuses) {
            const img = new Image();
            img.src = status['img'];
        }

        // Load DOM elements        
        const el = document.getElementById('live-status');
        const loadingIndicator = el.querySelector('p');
        const div = el.querySelector('div');
        const time = el.querySelector('time');
        const tbody = el.querySelector('tbody');
        const rowTemplate = document.getElementById('status-row');
        if (el == null || loadingIndicator == null || div == null || time == null || tbody == null || rowTemplate == null) {
            throw new Error('Missing HTMLElement');
        }

        // Fetch data from API
        const response = await fetch('/api');
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const results = await response.json();
        if (results.length == 0) {
            throw new Error('No results');
        }        
        
        // Add results to table
        const lang = document.documentElement.lang
        for (const res of results) {
            const clone = rowTemplate.content.cloneNode(true);
            const td = clone.querySelector('td');
            td.textContent = res['bay_id'];
            const img = clone.querySelector('img');
            const status = statuses[res['status']];
            img.setAttribute('src', status['img']);
            img.setAttribute('alt', status['alt'][lang]);
            const figcaption = clone.querySelector('figcaption');
            figcaption.textContent = status['text'][lang];
            tbody.appendChild(clone);
        }

        // Parse last updated time
        const timestamp = results[0]['timestamp'];
        const date = new Date(timestamp * 1000);
        const localTime = date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            timeZone: 'America/Los_Angeles',
            hour12: true
        });
        time.setAttribute('datetime', date.toISOString());
        time.textContent = localTime;
        
        // Reveal
        loadingIndicator.remove();
        div.classList.remove('hidden');
        div.setAttribute('aria-hidden', 'false');
    } catch (err) {
        console.error(err);
    }
})();
