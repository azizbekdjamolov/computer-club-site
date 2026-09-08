document.addEventListener('DOMContentLoaded', function () {
    // ---- Quick start modal ----
    const quickStartBtn = document.getElementById('quickStartBtn');
    const quickModal = document.getElementById('quickModal');

    function openModal(id) { const el = document.getElementById(id); if (el) el.classList.add('open'); }
    window.closeModal = function () {
        document.querySelectorAll('.modal-backdrop').forEach(function (m) { m.classList.remove('open'); });
    };
    if (quickStartBtn && quickModal) {
        quickStartBtn.addEventListener('click', function () { openModal('quickModal'); });
    }

    // Escape to close modals
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeModal();
    });
    document.querySelectorAll('.modal-backdrop').forEach(function (m) {
        m.addEventListener('click', function (e) {
            if (e.target === m) m.classList.remove('open');
        });
    });

    // ---- Dynamic computers for quick form ----
    const qsRoom = document.getElementById('qsRoom');
    const qsComputer = document.getElementById('qsComputer');
    if (qsRoom && qsComputer) {
        qsRoom.addEventListener('change', function () {
            const rid = this.value;
            qsComputer.innerHTML = '<option value="">Yuklanmoqda...</option>';
            if (!rid) { qsComputer.innerHTML = '<option value="">-- Avval xonani tanlang --</option>'; return; }
            fetch('/rooms/' + rid + '/computers/')
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    qsComputer.innerHTML = '<option value="">-- Kompyuter --</option>';
                    data.computers.forEach(function (pc) {
                        if (pc.status !== 'occupied') {
                            const o = document.createElement('option');
                            o.value = pc.id;
                            o.textContent = pc.name + (pc.status === 'reserved' ? ' (rezerv)' : pc.status === 'maintenance' ? ' (nosoz)' : ' (bo\'sh)');
                            qsComputer.appendChild(o);
                        }
                    });
                })
                .catch(function () { qsComputer.innerHTML = '<option value="">Xatolik</option>'; });
        });
    }

    // ---- Prefill start time in quick modal ----
    const qsStart = document.getElementById('qsStart');
    if (qsStart && !qsStart.value) {
        const now = new Date();
        const pad = function (n) { return String(n).padStart(2, '0'); };
        qsStart.value = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate()) +
            'T' + pad(now.getHours()) + ':' + pad(now.getMinutes());
    }

    // ---- Auto-fill duration -> end time (and vice versa) ----
    const duration = document.getElementById('qsDuration');
    const qsEnd = document.getElementById('qsEnd');
    if (duration && qsEnd && qsStart) {
        function addMinutes(iso, mins) {
            const d = new Date(iso);
            d.setMinutes(d.getMinutes() + mins);
            const pad = function (n) { return String(n).padStart(2, '0'); };
            return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
                'T' + pad(d.getHours()) + ':' + pad(d.getMinutes());
        }
        duration.addEventListener('change', function () {
            if (this.value && qsStart.value) qsEnd.value = addMinutes(qsStart.value, parseInt(this.value));
        });
        qsEnd.addEventListener('change', function () {
            if (this.value && qsStart.value) {
                const ms = new Date(this.value) - new Date(qsStart.value);
                if (ms > 0) duration.value = Math.round(ms / 60000);
            }
        });
    }

    // ---- PC card click -> info modal ----
    const pcModal = document.getElementById('pcModal');
    const pcModalBody = document.getElementById('pcModalBody');
    const statusText = { available: "Bo'sh", occupied: 'Band', reserved: 'Rezerv', maintenance: 'Nosoz' };

    function fmtMoney(n) {
        return new Intl.NumberFormat('ru-RU').format(Math.round(n || 0)) + ' ' + (window.CURRENCY || 'UZS');
    }

    document.querySelectorAll('.pc-card').forEach(function (card) {
        card.addEventListener('click', function (e) {
            e.preventDefault();
            const id = card.dataset.id;
            const name = card.dataset.name;
            const status = card.dataset.status;
            const roomId = card.dataset.room;

            if (status === 'occupied') {
                fetch('/sessions/active/')
                    .then(function (r) { return r.text(); })
                    .catch(function () { return ''; })
                    .then(function () {
                        // Server-side detail is easier: just link to active sessions detail via search
                    });
                window.location.href = '/sessions/active/';
                return;
            }

            const timeInput = '<input type="datetime-local" name="start_time" id="pcStart" class="form-control" value="' + prefillNow() + '">';
            pcModalBody.innerHTML =
                '<div class="modal-head"><h3><i class="fas fa-desktop"></i> ' + name + '</h3>' +
                '<button class="modal-close" onclick="closeModal()">&times;</button></div>' +
                '<div class="pc-status-line"><span class="status-pill ' + status + '">' + (statusText[status] || status) + '</span></div>' +
                '<form method="post" action="' + window.QUICK_URL + '" id="pcStartForm">' +
                '<input type="hidden" name="csrfmiddlewaretoken" value="' + window.CSRF + '">' +
                '<input type="hidden" name="room" value="' + roomId + '">' +
                '<input type="hidden" name="computer" value="' + id + '">' +
                '<div class="form-group"><label>Mijoz ismi</label>' +
                '<input type="text" name="customer_name" class="form-control" required placeholder="Ali Valiyev"></div>' +
                '<div class="form-group"><label>Telefon</label>' +
                '<input type="text" name="phone" class="form-control" placeholder="998901234567"></div>' +
                '<div class="form-row"><div class="form-group"><label>Boshlanish</label>' + timeInput + '</div>' +
                '<div class="form-group"><label>Davomiylik (daq)</label>' +
                '<input type="number" name="duration_minutes" class="form-control" min="1"></div></div>' +
                '<div class="form-row"><div class="form-group"><label>Tugash vaqti</label>' +
                '<input type="datetime-local" name="planned_end_time" class="form-control"></div>' +
                '<div class="form-group"><label>To\'lov</label>' +
                '<input type="number" name="paid_amount" class="form-control" min="0"></div></div>' +
                '<button type="submit" class="btn btn-primary btn-block btn-lg"><i class="fas fa-play"></i> START SESSION</button>' +
                '</form>';
            openModal('pcModal');
        });
    });

    function prefillNow() {
        const now = new Date();
        const pad = function (n) { return String(n).padStart(2, '0'); };
        return now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate()) +
            'T' + pad(now.getHours()) + ':' + pad(now.getMinutes());
    }
    window.prefillNow = prefillNow;
    window.fmtMoney = fmtMoney;

    // ---- Auto refresh ----
    if (window.AUTO_REFRESH && AUTO_REFRESH > 0) {
        setInterval(function () {
            if (document.querySelector('.global-search input') && document.activeElement === document.querySelector('.global-search input')) return;
            const path = window.location.pathname;
            if (path === '/' || path === '/sessions/active/') {
                location.reload();
            }
        }, AUTO_REFRESH * 1000);
    }
});