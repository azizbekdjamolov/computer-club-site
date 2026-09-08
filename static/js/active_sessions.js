document.addEventListener('DOMContentLoaded', function () {
    const cards = document.querySelectorAll('.active-card');
    cards.forEach(function (card) {
        const startMillis = new Date(card.dataset.start).getTime();
        const pricePerHour = parseFloat(card.dataset.price);
        const method = card.dataset.method;
        const fixedDur = parseInt(card.dataset.duration);
        const paid = parseFloat(card.dataset.paid) || 0;

        const secondsEl = card.querySelector('.js-elapsed');
        const priceEl = card.querySelector('.js-price');
        const remainingEl = card.querySelector('.js-remaining');

        function money(n) {
            return new Intl.NumberFormat('ru-RU').format(Math.round(n || 0)) + ' ' + (window.CURRENCY || 'UZS');
        }

        function calcPrice(minutes) {
            if (method === 'per_minute') {
                return (pricePerHour / 60) * minutes;
            }
            if (method === 'fixed') {
                return (pricePerHour / 60) * fixedDur;
            }
            const perMin = pricePerHour / 60;
            let amount = perMin * minutes;
            if (minutes < 60 && amount < pricePerHour) return pricePerHour; // first hour minimum
            return amount;
        }

        function compute() {
            const now = Date.now();
            let sec = Math.floor((now - startMillis) / 1000);
            if (sec < 0) sec = 0;
            const h = String(Math.floor(sec / 3600)).padStart(2, '0');
            const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
            const s = String(sec % 60).padStart(2, '0');
            if (secondsEl) secondsEl.textContent = h + ':' + m + ':' + s;

            const minutes = Math.floor(sec / 60);
            const total = calcPrice(minutes);
            if (priceEl) priceEl.textContent = money(total);

            if (remainingEl) {
                const remaining = total - paid;
                remainingEl.textContent = remaining > 0 ? money(remaining) : '0';
            }
        }
        compute();
        setInterval(compute, 1000);
    });
});